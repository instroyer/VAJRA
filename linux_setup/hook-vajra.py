# PyInstaller hook for VAJRA packages
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules from both packages
hiddenimports = collect_submodules('modules') + collect_submodules('core')

# Collect data files if any
datas = collect_data_files('modules') + collect_data_files('core')
