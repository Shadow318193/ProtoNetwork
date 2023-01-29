import os
import shutil

PYTHONANYWHERE = False

if __name__ == "__main__":
    if PYTHONANYWHERE:
        if os.getcwd() == "/home/Shadow318193":
            os.chdir("/home/Shadow318193/mysite")
    if os.path.isfile("db/social_network.db"):
        shutil.copyfile("db/social_network.db", "db/social_network_backup.db")
        print("Резервная копия базы данных сделана")
    else:
        print("Ошибка: нет базы данных")