from http.server import BaseHTTPRequestHandler
import h3
import simplekml
from math import log 
from urllib.parse import urlparse, unquote

def geth3polys(lat,lng,alt,lws=1.0,lwl=2.0,pcs='ff008000',pcl='ff0000ff',pos=2,pol=1):

    res=int(-1.044 * log(float(alt)) + 15.861)
    rings=int(26.097 * pow(float(alt),-0.17) )
    kml=simplekml.Kml()
    kml.document.name = 'DynamicKML'
    mpoly = kml.newmultigeometry()
    mpoly.name='h3hex'

    mpoly_hr = kml.newmultigeometry()
    mpoly_hr.name='h3hex_highres'

    # generate the larger hex rings centered around the cameras center of view
    home_hex=h3.geo_to_h3(lng,lat,res)#12)
    ring=h3.k_ring(home_hex,rings)
    for h in ring:
        gjhex=h3.h3_to_geo_boundary(h,geo_json=True)
        poly=mpoly.newpolygon(extrude=True,
                                outerboundaryis=gjhex)
        poly.style.linestyle.width = lwl
        poly.style.polystyle.color = simplekml.Color.changealphaint(pol, pcl)    

    # generate the smaller hex rings centered around the cameras center of view
    home_hex_small=h3.geo_to_h3(lng,lat,res+1)#12)
    ring_small=h3.k_ring(home_hex_small,3)
    for h in ring_small:
        gjhex=h3.h3_to_geo_boundary(h,geo_json=True)
        poly=mpoly_hr.newpolygon(extrude=True,
                                outerboundaryis=gjhex)
        poly.style.linestyle.width = lws
        poly.style.polystyle.color = simplekml.Color.changealphaint(pos, pcs)
    

    # create the screen overlay to display the current h3 resolution
    osd=kml.newscreenoverlay()
    osd.name='Resolution'
    osd.overlayxy = simplekml.OverlayXY(x=0,y=1,xunits=simplekml.Units.fraction,
                                       yunits=simplekml.Units.fraction)
    osd.screenxy = simplekml.ScreenXY(x=15,y=50,xunits=simplekml.Units.pixels,
                                     yunits=simplekml.Units.insetpixels)
    # cannot figure out how to just put text so this is silly but generate image from text
    osd.icon.href='http://chart.apis.google.com/chart?chst=d_text_outline&chld=FFBBBB|24|h|BB0000|b|'+'R'+str(res)+' '+'R'+str(res+1)
        
    return kml.kml()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print('GET')
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        #self.send_header('Content-type', 'application/vnd.google-earth.kmz')
        #self.send_header('Content-type', 'application/vnd.google-earth.kml+xml')
        
        self.end_headers()
        print(self.path)
        query = urlparse(self.path).query
        query=unquote(query)
        bbox,alt,aa,lws,lwl,pcs,pcl,pos,pol=query.split(';')

        aa = aa.split('AA=')[1]
        lws= lws.split('LWS=')[1]
        lwl= lwl.split('LWL=')[1]
        pcs= pcs.split('PCS=')[1]
        pcl= pcl.split('PCL=')[1]
        pos= pos.split('POS=')[1]
        pol= pol.split('POL=')[1]

        # get the altitude of the camera
        alt = float(alt.split('CAMERA=')[1])
        west,south,east,north=bbox.split('BBOX=')[1].split(',')
    
        # find the center of the map and the altitude
        west = float(west)
        south = float(south)
        east = float(east)
        north = float(north)

        lng = ((east - west) / 2) + west
        lat = ((north - south) / 2) + south
        polykml=geth3polys(lng,lat,float(alt + float(aa)),float(lws),float(lwl),str(pcs),str(pcl),int(pos),int(pol) )

        # send the new kml back to google earth
        self.wfile.write(polykml.encode('utf-8'))
        return