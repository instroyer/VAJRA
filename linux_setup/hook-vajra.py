# PyInstaller hook for VAJRA packages
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect submodules

# Collect data files if any
datas = collect_data_files('modules') + collect_data_files('core')
