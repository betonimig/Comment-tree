sudo apt-get install postgresql-contrib

# создание базы
sudo -u postgres psql -c "DROP DATABASE IF EXISTS comment_tree"
sudo -u postgres psql -c "DROP ROLE IF EXISTS comment_user"
sudo -u postgres psql -c "CREATE DATABASE comment_tree;"
sudo -u postgres psql -c "CREATE ROLE comment_user WITH LOGIN ENCRYPTED PASSWORD '[etvjtcomm';"
sudo -u postgres psql -c "ALTER DATABASE comment_tree OWNER TO comment_user ;"
--- подключаем ltree
sudo -u postgres psql -d comment_tree -c "CREATE EXTENSION ltree ;"

cat sql/create_db.sql | psql -d comment_tree -U comment_user -a 

virtualenv --python=python3 ./env
. ./env/bin/activate
pip install -r requirements.txt

echo "Заполняем тестовыми данными"
# аполнение тестовыми данными
python ./sql/insert_data.py

echo "Успех!"

echo "Добавьте директорию в PYTHONPATH: export PYTHONPATH=`pwd`"
echo "Для запуска используй: python -m comment_tree.main"