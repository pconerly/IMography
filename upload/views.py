#By Peter Conerly, 2/14/2011 based off code written in december
# Create your views here.
import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django import forms
import os
#import some hash stuff
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
#for ima_process
import time
import lxml.html.soupparser
import lxml.etree
#for sparklines
import Image, ImageDraw, ImageFont
from myproject.upload.models import AimLog #models!

def index(request):
    t = loader.get_template('index.html')
    c = RequestContext(request, {'foo': 'bar'})
    r = t.render(c)
    return HttpResponse(r)

def test_data(request, loghash):
    projectpath = os.path.abspath(os.path.split(__file__)[0])
    path = os.path.join(projectpath, 'media', str(loghash) + '.txt')
    if os.path.isfile(path):
        fin = open(path, 'r')
        data = fin.read()
        fin.close()
        html = "<html><body>Here is the file's data!<p>%s</p></body></html>" % data
        return HttpResponse(html)
    else:
        return HttpResponse('invalid hash')
        #return render_to_response('invalid.html')

def data(request, loghash):
    try:
        temp = AimLog.objects.filter(hash=loghash)
        log = temp[len(temp)-1] #negative index is not supported, so try this
    except AimLog.DoesNotExist:
        return HttpResponse('invalid hash')
    t = loader.get_template('data.html')
    templatelog = {'name': log.name,
                   'hash': log.hash,
                   'local': log.local,
                   'remote': log.remote,
                   'total': log.total,
                   'max': log.max,
                   'startyear': log.startyear,
                   'stopyear' : log.stopyear, }
    c = RequestContext(request, {'log': templatelog} )
    r = t.render(c)
    return HttpResponse(r)

def data_missing(request): #, badhash):
    return HttpResponse('your hash was invalid') # % badhash)

def success(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)

class UploadFileForm(forms.Form):
    file = forms.FileField()
    
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            loghash = ima_process(request.FILES['file'])
            url = '/data/' + loghash + '/'
            return HttpResponseRedirect(url) #change this to '/data/#hash' later
    else:
        form = UploadFileForm()
    return render_to_response('upload.html', {'form':form}, 
                              context_instance=RequestContext(request))

def ima_process(logfile):
    log = AimLog()
    log.name = logfile.name
    if log.name[-5:] != ".html" or log.name[0:4] == "conf": #check logfile.name
        return None
    data = logfile.read()
    #do hashing
    m = md5()
    m.update(data)
    log.hash = m.hexdigest()
    
    #process data!
    #wrapping the serious processing with a timer
    ptime = 0 - time.clock()
    try:
        root = lxml.html.soupparser.fromstring(data)
        log.local, log.remote = findusernames(root)
        chat = findchat(root)
        log.total = calculate_total(chat)
        log.max = calculate_globalmax(chat)
        log.startyear = chat[0][0].tm_year
        log.startday = chat[0][0].tm_yday
        log.stopyear = chat[-1][0].tm_year
        log.stopday = chat[-1][0].tm_yday
        log.save()
    except TypeError:
        print "=========="
        print "this file failed the beautiful soup parsing"
        print name
        print "=========="
    ptime += time.clock()
    #close file when i don't need it anymore
    logfile.close()
    if ptime > 1:
        print "file took", ptime
    data_store(chat, log.hash)
    plot_sparkline(chat, log)
    return log.hash

def plot_sparkline(chat, log, height = 100, width = 2):
    """Saves a sparkline image into the imstatic folder.
        Reminder of the format of chat:
        chat[i][0].tm_year, chat[i][0].tm_yday, chat[i][1] is count
    """
    h = ((log.stopyear - log.startyear + 1) * height) + 2
    im = Image.new("RGB", (366*width, h), 'white')
    draw = ImageDraw.Draw(im)
    color = "red"
    font = ImageFont.truetype("/usr/share/fonts/third-party-fonts-1.0/arial.ttf", 15)
    #draw a grey box around it
    draw.line((0, 0, 366*width, 0), fill="gray")
    draw.line((0, 0, 0, h-1), fill="gray")
    draw.line((366*width-1, 0, 366*width-1, h-1), fill="gray")
    for i in range(log.stopyear - log.startyear + 1):
        draw.line((0, height*(i+1)+1,
                  366*width,height*(i+1)+1),
                  fill="gray")        
        draw.text((10, (height*i)+10), str(log.startyear + i), font=font, fill='gray')
    for i in xrange(len(chat)):
        draw.line((width*chat[i][0].tm_yday - 1,
                   height*(chat[i][0].tm_year - log.startyear + 1),
                   width*chat[i][0].tm_yday - 1,
                   height*(chat[i][0].tm_year - log.startyear + 1) -
                   (height-2)*(float(chat[i][1])/ log.max) + 1 ),
                  fill=color)
    del draw
    projectpath = os.path.abspath(os.path.split(__file__)[0])
    im.save(os.path.join(projectpath, '..', '..', '..',
                         'imstatic', 'images', log.hash + '.png'),
            'PNG')
    return True
                
def daysinyear(year): #to deal with leap years
    if year % 4 == 0 and year % 400 != 0:
        return 366
    return 365

def data_store(chat, loghash):  #Now I get to store my own data format
    #I am not using this data at the moment, because temp_process creates the images
    #But if I ever want to re-plot images, I will need to use this data.
    #I imagine the urls.py would look something like:
    # ('^recalc/([0-9a-f]{32})/$', myproject.upload.views.recalc'),
    root = lxml.etree.Element("root")
    for i in xrange(len(chat)):
        root.append(lxml.etree.Element('date', count=str(chat[i][1])))
        root[i].text = str(chat[i][0].tm_year) + ", " + str(chat[i][0].tm_yday)

    projectpath = os.path.abspath(os.path.split(__file__)[0])
    path = os.path.join(projectpath, 'media', loghash + '.txt')
    fout = open(path, 'w')
    fout.write(lxml.etree.tostring(root, pretty_print=True))
    fout.close()
    return True

def findchat(root):
    #Structure of of record:
    #A list of [time, words]
    lasttime = ''
    lastwords = 0
    record = []
    chat = root[1][1][1]
    for i in xrange(len(chat)):
        if chat[i][0].attrib["class"] == "time":
            #TIME FORMAT <tr><td colspan="2" class="time">Wednesday, December 08, 2010</td></tr>
            if lasttime != '':
                record.append([lasttime, lastwords])
                lastwords = 0
            lasttime = time.strptime(chat[i][0].text, "%A, %B %d, %Y")
        if chat[i][0].attrib["class"] == "remote" or chat[i][0].attrib["class"] == "local":
            if len(chat[i][1]) == 0:
                if chat[i][1].text != None:
                    lastwords += len(chat[i][1].text.split())                
            else:
                for j in range(len(chat[i][1])):
                    if chat[i][1][j].text != None:
                        lastwords += len(chat[i][1][j].text.split())
                """prints the number of words in the message, depending on whether
                    there is a font html tag or not"""
    record.append([lasttime, lastwords])
    return record

def findusernames(root):
    body = root[1][1]
    temp = body[0][1].attrib["href"]
    temp = temp.split("=")
    print "local", temp[-1]
    print "remote", body[0][1].text
    return (temp[-1].lower(), body[0][1].text.lower()) #returns a tuple of (local, remote) usernames

def calculate_total(temp):
    total = 0
    for i in range(len(temp)):
        total += temp[i][1]
    return total

def calculate_globalmax(temp):
    globalmax = 0
    for i in range(len(temp)):
        if temp[i][1] > globalmax:
            globalmax = temp[i][1]
    return globalmax
