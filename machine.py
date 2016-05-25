#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import psycopg2
import psycopg2.extras
import time
import config
import argparse
import urllib
from time import gmtime, strftime
from osgeo import osr


def deb(string):
    return 0
    print string


def callOSMOT(host,dbname,user,password):
    cmd='''python osmot/osmot.py -hs '''+host+''' -d '''+dbname+''' -u '''+user+''' -p '''+password+'''
	'''
    print cmd
    os.system(cmd)



def cleardb(host,dbname,user,password):
        ConnectionString="dbname=" + dbname + " user="+ user + " host=" + host + " password=" + password

	try:

		conn = psycopg2.connect(ConnectionString)
	except:
		print 'Error. Unable to connect to the database' 
                print ConnectionString
		return 0
	cur = conn.cursor()
	sql ='''
	DROP TABLE IF EXISTS planet_osm_buildings 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_line 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_nodes 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_point 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_polygon 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_rels 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_roads 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_ways 		CASCADE;
	DROP TABLE IF EXISTS route_line_labels 		CASCADE;
	DROP TABLE IF EXISTS routes_with_refs 		CASCADE;
	DROP TABLE IF EXISTS terminals 			CASCADE;
	DROP TABLE IF EXISTS terminals_export 		CASCADE;
	'''

	cur.execute(sql)
	conn.commit()

def importdb(host,dbname,user,password, osmFileHandler):
	os.system('''
	osm2pgsql --create  --slim -E 3857 --database '''+dbname+''' --username '''+user+''' --password --port  5432 --host '''+host+''' --style default.style '''+osmFileHandler+'''
	''')

def makeOverpassQuery(currentmap):
    #https://github.com/mvexel/overpass-api-python-wrapper    

    data=  {'data':  '''[out:xml][timeout:55];(relation["route"="'''+currentmap['transport']+'''"]('''+currentmap['bbox_string']+'''););out meta;>;out meta qt;'''}
    print 'new '+urllib.unquote(urllib.urlencode(data)).decode('utf8')
    #return  'http://overpass.osm.rambler.ru/cgi/interpreter?'+urllib.urlencode(data)
    return  'http://overpass-api.de/api/interpreter?'+urllib.urlencode(data)


    #return query
def diffStatisticArrays(prev,current):

    diff={'deletedRoutesCount':0,'addedRoutesCount':0,'lenChange':0}
    return diff


def compareStatistic(cursor,currentmap):
    '''
    compare route len and routes count of already imported network with stattable for currentmap
    return array with statistic
    '''
    prev=getLastStatiscticLine(cursor)
    current=calcCurrentStatistic(cursor)
    diff=diffStatisticArrays(prev,current)
    diff={'deletedRoutesCount':0,'addedRoutesCount':0,'lenChange':0}
    result=False
    return result,diff

def writeStatistic(host,dbname,user,password,osmFileHandler,currentmap):
    '''
    save statistic of currently imported network
    '''
    current=calcCurrentStatistic(host,dbname,user,password,osmFileHandler,currentmap)
    #sql line of add current


    return 0

def calcCurrentStatistic(cursor):
    '''
    return array with statistic from osmot importted
    '''
    print 'calc' 
    try:
            cursor.execute('''



SELECT sum(ST_Length_Spheroid(ST_Transform(planet_osm_line.way,4326),'SPHEROID["WGS 84",6378137,298.257223563]'))/1000 
FROM
planet_osm_line,
(
SELECT

  unnest_rel_members_ways(members) as members 
from planet_osm_rels
WHERE 

tags::VARCHAR LIKE '%route,trolleybus%'
            OR tags::VARCHAR LIKE '%route,tram%'
            OR tags::VARCHAR LIKE '%route,bus%'
            OR tags::VARCHAR LIKE '%route,share_taxi%'
) AS unnestWays
WHERE unnestWays.members::bigint = planet_osm_line.osm_id;
                    ''')

    except:
            print 'error in lenRoutes calc'
            return 0
    rows = cursor.fetchall()
    for row in rows:
            lenRoutes = row[0]
    print 'lenroutes='+str(lenRoutes)

    try:
            cursor.execute('''
SELECT COUNT(*) from planet_osm_rels
WHERE 
tags::VARCHAR LIKE '%route,trolleybus%'
            OR tags::VARCHAR LIKE '%route,tram%'
            OR tags::VARCHAR LIKE '%route,bus%'
            OR tags::VARCHAR LIKE '%route,share_taxi%'
                    ''')

    except:
            print 'error in RoutesCount calc'
            return 0
    rows = cursor.fetchall()
    for row in rows:
            osmRoutesCount = row[0]
    print 'osmRoutesCount='+str(osmRoutesCount)


    #routesCount
    try:
            cursor.execute('''
SELECT
count (distinct substring(tags::varchar from 'ref,(.*?)[,}]')) AS ref
from planet_osm_rels
WHERE 
tags::VARCHAR LIKE '%route,trolleybus%'
            OR tags::VARCHAR LIKE '%route,tram%'
            OR tags::VARCHAR LIKE '%route,bus%'
            OR tags::VARCHAR LIKE '%route,share_taxi%'
ORDER BY ref
;
                    ''')

    except:
            print 'error in RoutesCount calc'
            return 0
    rows = cursor.fetchall()
    for row in rows:
            osmRefsCount = row[0]
    print 'osmRefsCount='+str(osmRefsCount)



    #routesRefsArray
    try:
        cursor.execute('''
SELECT ARRAY(SELECT * FROM
(
SELECT
DISTINCT SUBSTRING(tags::varchar from 'ref,(.*?)[,}]') AS ref
FROM planet_osm_rels
WHERE 
tags::VARCHAR LIKE '%route,trolleybus%'
            OR tags::VARCHAR LIKE '%route,tram%'
            OR tags::VARCHAR LIKE '%route,bus%'
            OR tags::VARCHAR LIKE '%route,share_taxi%') AS refs
ORDER BY NULLIF(regexp_replace(ref, E'\\D', '', 'g'), '')::int
)
;
                    ''')


        rows = cursor.fetchall()
        for row in rows:
                routesRefsArray = row[0]
    except:
            print 'error in routesRefsArray calc'
            routesRefsArray=''
    print 'routesRefsArray='+str(routesRefsArray)
        

    stat={'routeRefsArray':routesRefsArray,'osmRefsCount':osmRefsCount,'osmRoutesCount':osmRoutesCount,'lenNetwork':0,'lenRoutes':lenRoutes}
    return stat

def getLastStatiscticLine(cursor):
    '''
    return array with statistic from statistic table
    '''    
    #select * from statistic where id='' order by dt desc LIMIT 1;
    stat={'routeRefsArray':'{}','RoutesCount':0,'len':0}


def process():

    #Connect to DB
    host=config.host
    dbname=config.dbname
    user=config.user
    password=config.password

    #https://github.com/trolleway/osm-scripts/blob/master/milestone_generation/milestones_generation.py

    connectString="dbname='" + dbname + "' user='"+ user + "' host='" + host + "' password='" + password + "'"
    try:
         conn = psycopg2.connect(connectString)
    except:
         print 'Error. Unable to connect to the database while frist connect '+connectString
         return 0



    tmpfiles=dict()
    tmpfiles['lines'] = 'tmp/lines.png'
    tmpfiles['terminals'] = 'tmp/terminals.png'

    tmpfiles['stage1'] = 'tmp/stage1.tif'
    tmpfiles['background'] = 'tmp/background.png'
    #Query for active maps
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
SELECT CONCAT(
ST_YMin(Box2D(wkb_geometry)),',',
ST_XMin(Box2D(wkb_geometry)),',',
ST_YMax(Box2D(wkb_geometry)),',',
ST_XMax(Box2D(wkb_geometry))
) AS bbox_string,
CONCAT(
ST_XMin(Box2D(ST_Transform(wkb_geometry,3857))),' ',
ST_YMax(Box2D(ST_Transform(wkb_geometry,3857))),' ',
ST_XMax(Box2D(ST_Transform(wkb_geometry,3857))),' ',
ST_YMin(Box2D(ST_Transform(wkb_geometry,3857)))
) AS bbox_string_gdal
,
(
ST_Distance(
ST_PointN(Box2D(ST_Transform(wkb_geometry,3857)),1),
ST_PointN(Box2D(ST_Transform(wkb_geometry,3857)),2)
) 
/
ST_Distance(
ST_PointN(Box2D(ST_Transform(wkb_geometry,3857)),2),
ST_PointN(Box2D(ST_Transform(wkb_geometry,3857)),3)
) )AS aspect,
*
from meta.maps
ORDER BY map_id;

                ''')
    rows = cur.fetchall()
    for currentmap in rows:
        print currentmap['map_id']



        doPpreprocessing = False
        if doPpreprocessing == True:
            
            #Make overpass-api query
            overpass_query=makeOverpassQuery(currentmap)
            #print overpass_query
            
            #Do overpass query
            osmFileHandler='tmp/data.osm'

            #urllib.urlretrieve(overpass_query,osmFileHandler)

            #osmFileHandler=doOverpassQuery(overpass_query)
            #Drop tables in DB
            cleardb(host,dbname,user,password)
            

            #call osm2pgsql
            importdb(host,dbname,user,password,osmFileHandler)
            
            #call osmot - do preprocessin
            callOSMOT(host,dbname,user,password)
                
        #stat = calcCurrentStatistic(cur)   
        compareResult, stat=compareStatistic(cur,currentmap)
        compareResult = True
        if (compareResult == False):
            print 'not intresting'
            continue
        
            
        #stage1 - simple png picture

        gdalcmd='gdal_translate -of "GTiff" -a_nodata 0 -co ALPHA=YES -outsize '+currentmap['size_px']+' -r lanczos -projwin  '+currentmap['bbox_string_gdal']+'   gdal_wms/wmsosmot.xml '+tmpfiles['stage1']
        print gdalcmd
        os.system( gdalcmd)      

        gdalcmd='gdal_translate -of "PNG" -outsize '+currentmap['size_px']+' -r lanczos -projwin  '+currentmap['bbox_string_gdal']+'   gdal_wms/wmsosm.xml '+tmpfiles['background']
        print gdalcmd
        os.system( gdalcmd)   
      

        import Image

        background = Image.open(tmpfiles['background'])
        overlay = Image.open(tmpfiles['stage1'])

        background = background.convert("RGBA")
        overlay = overlay.convert("RGBA")

        background.paste(overlay, (0, 0), overlay)
        #new_img = Image.blend(background, overlay, 0.5)
        background.save("stage02.png","PNG")
        
        fileDateStrinng=strftime('%Y-%m-%d %H%M%S', gmtime())
        os.rename("stage02.png",os.path.join('output',currentmap['map_id']+' MAP '+fileDateStrinng+'.png'))


        #imgs=dict()
        #imgs['lines']=config.ngw_url+'/api/component/render/image?resource=19&extent='+currentmap['bbox_string_3857']+'&size='+currentmap['size_px']
        #imgs['terminals']=config.ngw_url+'/api/component/render/image?resource=17&extent='+currentmap['bbox_string_3857']+'&size='+currentmap['size_px']

        

        #wms_full_url=config.wms_url+'?request=GetMap&service=WMS&version=1.1.1&layers=tram_lines,tram_terminals&srs=EPSG%3A3857&bbox='+currentmap['bbox_string_3857']+'&width=2000&height=2000&format=image%2Fpng'
        #print wms_full_url
        #urllib.urlretrieve(wms_full_url,tmpfiles['stage1'])



        quit()
    #http://192.168.122.94:6543/api/component/render/image?resource=19&extent=4295359.6946304,7364898.7668221,4334992.2937908,7389205.7418135&size=1037,636'
    #wms url
    #http://192.168.122.94:6543/api/resource/52/wms?request=GetMap&service=WMS&version=1.1.1&layers=tram_lines,tram_terminals&srs=EPSG%3A3857&bbox=4295359.6946304,7364898.7668221,4334992.2937908,7389205.7418135&&width=2000&height=2000&format=image%2Fpng


        '''
        gdalinfo "<GDAL_WMS><Service name=\"osmot\"><ServerUrl>http://192.168.122.94:6543/api/resource/52/wms</ServerUrl><TiledGroupName>GroupNane</TiledGroupName></Service></GDAL_WMS>"
        gdal_translate "http://192.168.122.94:6543/api/resource/52/wms/" wms.xml -of WMS

        gdal_translate -of "GTIFF" -outsize 100 100 -projwin_srs 3857 -projwin 4295359.6946304 7389205.7418135 4334992.2937908 7364898.7668221 wmsosmot.xml test.tiff

        gdal_translate -of "GTIFF" -outsize 1000 1000  -projwin 4295359.6946304 7389205.7418135 4334992.2937908 7364898.7668221 wmsosmot.xml test.tiff

        gdal_translate -of "GTIFF" -outsize 1000 1000  -projwin 30 55 35 54  wmsosmot.xml test.tiff

        http://192.168.122.94:6543/api/resource/52/wms?service=WMS&request=GetMap&version=1.1.1&layers=tram_lines&styles=&srs=EPSG:3857&format=image/png&width=512&height=512&bbox=28.00000000,50.00000000,36.00000000,58.00000000

        
        urllib.urlretrieve(imgs['lines'],tmpfiles['lines'])
        print imgs['lines']
        urllib.urlretrieve(imgs['terminals'],tmpfiles['terminals'])
        '''
        
        quit()
        #stage2 - simple png picture with minimaps
        #stage3 - simple png picture with legend
        #stage4 - multi-page pdf
        #Post picture to social networks
        post2filckr(imagefile)
        

        #возможно - сохраняем в постоянной БД с обновлением, если придумаем как

        #image generation from our WFS
        #call osmot for multipage atlas
        #get atlas pages from WFS
        #create multipage pdf with atlas


if __name__ == '__main__':
	process()
