#testarossa_deploy
#virt ip: 192.168.122.94
#ngw http://192.168.122.94:6543
#wms http://192.168.122.94:6543/api/resource/52/wms
#user: gisuser JeTLDEmM
#postgis gisusr gisuser
#: ngw_admin TmIt0Yx5

sudo apt-get install postgresql postgresql-contrib postgis

sudo service postgresql restart


#Установить PostGIS:

sudo apt-cache search postgis

#В полученном списке найдите пакет, подходящий для вашей версии PostgreSQL, его имя должно иметь вид postgresql-{version}-postgis-{version} и установите его:

sudo apt-get install postgresql-9.3-postgis-2.1

#remote access to postgresql
sudo nano /etc/postgresql/9.3/main/postgresql.conf
#to
#listen_addresses='*'

sudo nano /etc/postgresql/9.3/main/pg_hba.conf
#and add
#
#host all all * md5



sudo invoke-rc.d postgresql restart
sudo invoke-rc.d postgresql reload


sudo -u postgres createuser gisuser -P -e
#edit here 
sudo nano /etc/postgresql/9.3/main/pg_hba.conf

sudo -u postgres createdb -O gisuser --encoding=UTF8 osmot

sudo -u postgres psql -d osmot -c 'CREATE EXTENSION postgis;'


sudo -u postgres psql -d osmot 
CREATE ROLE trolleway SUPERUSER  password 'trolleway';
ALTER ROLE trolleway WITH login;

sudo -u postgres psql -d osmot -c 'ALTER TABLE geometry_columns OWNER TO gisuser;'
sudo -u postgres psql -d osmot -c 'ALTER TABLE spatial_ref_sys OWNER TO gisuser;'
sudo -u postgres psql -d osmot -c 'ALTER TABLE geography_columns OWNER TO gisuser;'

#После этих операций будут созданы БД PostgreSQL с установленным в ней PostGIS и пользователь БД, который станет ее владельцем, а также таблиц geometry_columns, georgaphy_columns, spatial_ref_sys.

#Убедитесь, что функции PostGIS появились в базе:

psql -h localhost -d osmot -U gisuser -c "SELECT PostGIS_Full_Version();"
sudo apt-get install osm2pgsql
cd ~
mkdir osmot
cd osmot

#install ngw
sudo apt-get update
sudo apt-get install software-properties-common python-software-properties
sudo apt-add-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt-get update
sudo apt-get upgrade

sudo -u postgres createuser ngw_admin -P -e
sudo -u postgres createdb -O ngw_admin --encoding=UTF8 db_ngw

sudo apt-get install python-pip
sudo pip install virtualenv
sudo apt-get install python-mapscript python-dev git libgdal-dev python-dev \
g++ libxml2-dev libxslt1-dev gdal-bin libgeos-dev zlib1g-dev libjpeg-turbo8-dev
mkdir -p ~/ngw/{data,upload}
cd ~/ngw
git clone https://github.com/nextgis/nextgisweb.git
virtualenv --no-site-packages env


env/bin/pip install git+https://github.com/geopython/OWSLib.git

#прописать в nextgisweb/setup.py owslib со знаком >=

env/bin/pip install -e ./nextgisweb
sudo apt-get install python-mapscript
mkdir env/lib/python2.7/site-packages/mapscript.egg
cp /usr/lib/python2.7/dist-packages/*mapscript* \
env/lib/python2.7/site-packages/mapscript.egg
echo "./mapscript.egg" > env/lib/python2.7/site-packages/mapscript.pth
env/bin/pip freeze
mkdir env/lib/python2.7/site-packages/mapscript.egg/EGG-INFO
touch env/lib/python2.7/site-packages/mapscript.egg/EGG-INFO/PKG-INFO
echo `python -c "import mapscript; print 'Version: %s' % mapscript.MS_VERSION"` \
> env/lib/python2.7/site-packages/mapscript.egg/EGG-INFO/PKG-INFO


git clone https://github.com/nextgis/nextgisweb_mapserver.git
env/bin/pip install -e ./nextgisweb_mapserver
env/bin/pip freeze

env/bin/nextgisweb-config > config.ini

#create development.ini

env/bin/pserve development.ini

#set passwords in ngw

#Для автоматического запуска NextGIS Web при загрузке операционной системы необходимо отредактировать пользовательский скрипт автозапуска:

sudo nano /etc/rc.local
#и добавить в него строку:

/home/zadmin/ngw/env/bin/pserve --daemon  /home/zadmin/ngw/production.ini

CREATE SCHEMA meta;

ogr2ogr -progress -f "PostgreSQL" PG:"host=192.168.122.94 dbname=osmot  user=trolleway active_schema=meta" "maps_init.geojson" -nln maps 

#Передаём на сервер скрипт импорта
#добавляем в веб слои
#вводим в конфиг ссылки на веб
mkdir tmp
sudo pip install -r requirements.txt


#install qgis
sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt-get update
sudo apt-get install qgis

cd ngw
git clone https://github.com/nextgis/nextgisweb_qgis.git
source env/bin/activate
pip install -e nextgisweb_qgis/


DST=`python -c "import sys; print sys.path[-2]"`
echo $DST
cp `/usr/bin/python -c "import sip; print sip.__file__"` $DST
cp -r `/usr/bin/python -c "import PyQt4, os.path; print os.path.split(PyQt4.__file__)[0]"` $DST
cp -r `/usr/bin/python -c "import qgis, os.path; print os.path.split(qgis.__file__)[0]"` $DST

dpkg -s qgis
#if >2.8 - see ngw_qgis docs for next instruction


добавляем функции postgresql

-- Function: unnest_rel_members_ways(anyarray)

-- DROP FUNCTION unnest_rel_members_ways(anyarray);

CREATE OR REPLACE FUNCTION unnest_rel_members_ways(anyarray)
  RETURNS SETOF anyelement AS
$BODY$SELECT substring($1[i] from E'w(\\d+)') FROM
generate_series(array_lower($1,1),array_upper($1,1)) i WHERE 
$1[i] LIKE 'w%' /*only ways*/
AND /*exclude platforms*/
($1[i+1] ='' 
OR $1[i+1] IN ('forward','backward','highway')
)
;$BODY$
  LANGUAGE sql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION unnest_rel_members_ways(anyarray)
  OWNER TO postgres;
GRANT EXECUTE ON FUNCTION unnest_rel_members_ways(anyarray) TO public;
GRANT EXECUTE ON FUNCTION unnest_rel_members_ways(anyarray) TO postgres;
GRANT EXECUTE ON FUNCTION unnest_rel_members_ways(anyarray) TO "osmot users";






gdal_translate -of "GTIFF" -outsize 1000 1000  -projwin  4143247 7497160 4190083 7468902   ngw.xml test.tiff
gdal_translate -of "GTIFF" -outsize 1000 1000  -projwin  4131491 7550235 4253599 7468050   ngw.xml test.tiff
gdal_translate -of "GTIFF" -outsize 1000 1000  -projwin  4010164 7630600 4498594 7301859   wmsosmot.xml test.tiff


Скрипт берёт из базы охват, и выкачивает его по оверпасу
Дропает схему
импортирует маршруты в базу
Запускает осмот
возможно копирует в постоянную схему
генерирует картинку через веб
постит картинку
