import hashlib

with open('config.json','rb') as  file:
    f = file.read()
    m = hashlib.md5()
    m.update(f)
    print(m.hexdigest())
with open('config.json.bak','rb') as  file:
    f = file.read()
    m = hashlib.md5()
    m.update(f)
    print(m.hexdigest())