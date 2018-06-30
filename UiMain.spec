# -*- mode: python -*-
from sys import setrecursionlimit
setrecursionlimit(5000)
block_cipher = None
added_files = [
         ( 'SAIC_Temp.pptx', '.' ),
         ( 'qt.conf', '.'),
         ( 'platforms', 'platforms'),
         ( 'bin', 'bin')
         ]
a = Analysis(['UiMain.py'],
             pathex=['C:\\Users\\Lu\\PycharmProjects\\SystemGain',
                     'C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x86',
                     'C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x64'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='UiMain',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='UiMain')
