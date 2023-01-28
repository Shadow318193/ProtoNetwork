import os
import shutil

if __name__ == "__main__":
    if os.path.isfile("db/social_network.db"):
        shutil.copyfile("db/social_network.db", "db/social_network_backup.db")
        print("Резервная копия базы данных сделана")
    else:
        print("Ошибка: нет базы данных")