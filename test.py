import bcrypt
salt = bcrypt.gensalt()
print(bcrypt.hashpw("test", salt), salt)