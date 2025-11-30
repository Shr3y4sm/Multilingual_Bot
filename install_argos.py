import argostranslate.package as pkg
available = pkg.get_available_packages()
pairs = [('en','hi'),('en','kn'),('en','ta'),('en','te'),('en','mr'),
         ('en','bn'),('en','gu'),('en','pa'),('en','ur')]
installed = 0
for fr,to in pairs:
    cand = [p for p in available if p.from_code==fr and p.to_code==to]
    if cand:
        p = cand[0]
        print('Installing', p)
        path = p.download()
        pkg.install_from_path(path)
        installed += 1
print('Installed packs:', installed)
