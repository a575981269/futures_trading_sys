"""
GUI应用程序入口
"""
import sys
import os
import json
import time

# #region agent log
_log_path = r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log'
with open(_log_path, 'a', encoding='utf-8') as f:
    _venv_path = os.environ.get('VIRTUAL_ENV', 'NOT_SET')
    _python_exe = sys.executable
    _venv_in_path = any('venv' in p for p in sys.path)
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"VENV","location":"gui/main.py:11","message":"Virtual env check","data":{"sys_path":sys.path,"cwd":os.getcwd(),"__file__":__file__ if '__file__' in globals() else "NOT_SET","argv":sys.argv,"VIRTUAL_ENV":_venv_path,"python_exe":_python_exe,"venv_in_path":_venv_in_path},"timestamp":int(time.time()*1000)})+'\n')
# #endregion

# Hypothesis A: __file__ is relative path, need absolute path
# Hypothesis B: Project root calculation is wrong
# Hypothesis C: sys.path doesn't include project root when running gui/main.py directly
# Hypothesis D: __file__ might not exist in some execution contexts
# Hypothesis E: Import happens before path fix is applied

# Fix: Add project root to sys.path
try:
    _script_file = __file__
except NameError:
    # #region agent log
    with open(_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"gui/main.py:25","message":"__file__ not defined","data":{},"timestamp":int(time.time()*1000)})+'\n')
    # #endregion
    _script_file = os.path.abspath(sys.argv[0])

# #region agent log
with open(_log_path, 'a', encoding='utf-8') as f:
    _abs_file = os.path.abspath(_script_file)
    _script_dir = os.path.dirname(_abs_file)
    _project_root = os.path.dirname(_script_dir)
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"gui/main.py:33","message":"Path calculation","data":{"script_file":_script_file,"abs_file":_abs_file,"script_dir":_script_dir,"project_root":_project_root,"gui_dir":os.path.join(_project_root,'gui'),"gui_exists":os.path.exists(os.path.join(_project_root,'gui')),"gui_init_exists":os.path.exists(os.path.join(_project_root,'gui','__init__.py'))},"timestamp":int(time.time()*1000)})+'\n')
# #endregion

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(_script_file)))

# #region agent log
with open(_log_path, 'a', encoding='utf-8') as f:
    _before_path = sys.path.copy()
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"gui/main.py:42","message":"sys.path before insert","data":{"sys_path":sys.path,"project_root_in_path":_project_root in sys.path},"timestamp":int(time.time()*1000)})+'\n')
# #endregion

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# #region agent log
with open(_log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"gui/main.py:48","message":"sys.path after insert","data":{"sys_path":sys.path,"project_root":_project_root,"project_root_in_path":_project_root in sys.path,"can_import_gui":False},"timestamp":int(time.time()*1000)})+'\n')
    # Test if gui can be imported
    try:
        import importlib.util
        _gui_path = os.path.join(_project_root, 'gui', '__init__.py')
        if os.path.exists(_gui_path):
            _spec = importlib.util.spec_from_file_location("gui", _gui_path)
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gui/main.py:54","message":"gui module spec created","data":{"spec_exists":_spec is not None},"timestamp":int(time.time()*1000)})+'\n')
    except Exception as e:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gui/main.py:57","message":"Error testing gui import","data":{"error":str(e)},"timestamp":int(time.time()*1000)})+'\n')
# #endregion

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# #region agent log
with open(_log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gui/main.py:64","message":"About to import gui.main_window","data":{"sys_path":sys.path},"timestamp":int(time.time()*1000)})+'\n')
# #endregion

from gui.main_window import MainWindow
from gui.utils.theme import Theme
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("期货量化交易系统")
    app.setOrganizationName("FuturesTrading")
    
    # 应用主题
    Theme.apply_dark_theme(app)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


