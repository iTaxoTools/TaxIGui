from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("itaxotools.taxi_gui")

hiddenimports = collect_submodules(
    "itaxotools.taxi_gui.tasks", filter=lambda name: True
)
