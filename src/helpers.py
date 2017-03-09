# -*- coding: utf-8 -*-
#
# django-codenerix
#
# Copyright 2017 Centrologic Computational Logistic Center S.L.
#
# Project URL : http://www.codenerix.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# System
import os
from datetime import datetime
import random
from dateutil.tz import tzutc
import dateutil.parser
import zipfile
import StringIO
from unidecode import unidecode

# Django
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from django.template import TemplateDoesNotExist
from django.template.loader import get_template as django_get_template
from django.shortcuts import render
from django.conf import settings
from django.views.generic.base import View
from django.core.cache import cache

def epochdate(timestamp):
    '''
    Convet an epoch date to a tuple in format ("yyyy-mm-dd","hh:mm:ss")
    Example: "1023456427" -> ("2002-06-07","15:27:07")
    
    Parameters:
    - `timestamp`: date in epoch format
    '''
    
    dt = datetime.fromtimestamp(float(timestamp)).timetuple()
    fecha = "{0:d}-{1:02d}-{2:02d}".format(dt.tm_year, dt.tm_mon,dt.tm_mday)
    hora = "{0:02d}:{1:02d}:{2:02d}".format(dt.tm_hour,dt.tm_min,dt.tm_sec)
    return (fecha, hora)

def date2string(dtime,formt,default):
    if dtime:
        if ('year' in dir(dtime)) and (dtime.year<1900):
            return default
        elif type(dtime)==unicode:
            return dtime
        else:
            return dtime.strftime(formt)
    else:
        return default

def daterange_filter(value, variable):
    startt=value['startDate'].split("T")[0]
    endt=value['endDate'].split("T")[0]
    start=datetime.strptime(startt,settings.DATETIME_RANGE_FORMAT[0])
    end=datetime.strptime(endt,settings.DATETIME_RANGE_FORMAT[0])
    result={'{0}__gte'.format(variable):start,'{0}__lte'.format(variable):end}
    return result

def timezone_serialize(d, prettify=False):
    if d is None:
        result = None
    else:
        if d.tzinfo:
            d = d.astimezone(tzutc()).replace(tzinfo=None)
        if prettify:
            result = d.strftime(settings.DATETIME_INPUT_FORMATS[0])
        else:
            result = d.isoformat() + "Z"
    return result

def timezone_deserialize(string):
    if string is None:
        result = None
    else:
        result = dateutil.parser.parse(string)
    return result

def zeropad(number,width):
    return '{number:0{width}d}'.format(width=width, number=number)

def monthname(value):
    if   value==1:    return _("January")
    elif value==2:    return _("February")
    elif value==3:    return _("March")
    elif value==4:    return _("April")
    elif value==5:    return _("May")
    elif value==6:    return _("June")
    elif value==7:    return _("July")
    elif value==8:    return _("August")
    elif value==9:    return _("September")
    elif value==10:    return _("Octuber")
    elif value==11:    return _("November")
    elif value==12:    return _("December")
    else:
        return None


# Name unify
def nameunify(name, url=False):
    # Make unicode
    name = smart_unicode(name)
    
    # Get it on lower
    namelow = unidecode(name).lower()
    
    # Define valid characters
    allowed_characters = 'abcdefghijklmnopqrstuvwxyz0123456789_-'
    if url:
        namelow = namelow.replace(' ', "-")
    else:
        namelow = namelow.replace("-", "").replace(' ', '_')
    
    # Replace all unknown characters
    result = ''
    for c in namelow:
        if c in allowed_characters:
            result += c
    
    # Return the cleaned result
    return result


def get_profile(user):
    # Check if it has admin rights admin
    try:
        is_admin = bool(user.is_superuser or user.groups.get(name='Admins'))
    except:
        is_admin = False
    
    if is_admin:
        # Administrator use root
        profile="admin"
    else:
        profile=None
    
    # Return profile
    return profile

def get_profiled_paths(path,user,lang,extension):
    paths=[]
    if user:
        # Check if it has admin rights admin
        profile=get_profile(user)
        
        # Define the base_path to use
        paths.append("{0}.{1}".format(user.username,lang))
        paths.append(user.username)
        if profile:
            paths.append("{0}.{1}".format(profile,lang))
            paths.append(profile)
        if profile!='admin':
            paths.append("user.{0}".format(lang))
            paths.append('user')
    
    # Add an empty path
    paths.append(lang)
    paths.append("")
    
    # Split path name
    pathsp=path.split(".")
    if pathsp[-1]==extension:
        basepath=".".join(pathsp[:-1])
    else:
        basepath=path
    
    # Return paths and basepath
    return (paths,basepath)

def get_template(template,user,lang,extension='html', raise_error=True):
    # Get profiled paths
    (templates,templatepath)=get_profiled_paths(template,user,lang,extension)
    
    # Check templates
    test=[]
    found=None
    for temp in templates:
        if len(temp):
            addon=".%s" % (temp)
        else:
            addon=""
        target="%s%s.%s" % (templatepath,addon,extension)
        test.append(target)
        try:
            django_get_template(target)
            found=target
            break
        except TemplateDoesNotExist:
            pass
    
    # Return target template
    if found:
        return found
    else:
        if raise_error:
            raise IOError,"I couldn't find a valid template, I have tried: {}".format(test)
        else:
            return test

def get_static(desired,user,lang,default,extension='html'):
    # Get profiled paths
    (paths,basepath)=get_profiled_paths(desired,user,lang,extension)
    
    # Check paths
    found=None
    for temp in paths:
        if len(temp):
            addon=".%s" % (temp)
        else:
            addon=""
        target="%s%s.%s" % (basepath,addon,extension)
        if hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT and os.path.exists(os.path.join(settings.STATIC_ROOT, target)):
            found=target
            break
    
    # Return target template
    if found:
        # Return the one we found
        return found
    else:
        # We didn't find any, return default one
        return default

def direct_to_template(request,template):
    template=get_template(template,request.user)
    return render(request,template)

def model_inspect(obj,attributes=False):
        '''
        Analize itself looking for special information, right now it returns:
        - Application name
        - Model name
        - Attributes (not returned by default)
        '''
        # Prepare the information object
        info={}
        
        # Attributes dict & keys
        attributes_dict = dir(obj)
        
        # Get attributes list
        if attributes: info['attributes']=attributes_dict
        if hasattr(obj, '_meta'):
            info['verbose_name'] = getattr(obj._meta, 'verbose_name', None)
        else:
            info['verbose_name'] = None
        
        # Get info from the object
        if 'model' in  attributes_dict and obj.model:
            namesp=str(obj.model)
        else:
            namesp=str(obj.__class__)
        namesp = namesp.replace("<class ","").replace(">","").replace("'","").split(".")

        # Remember information
        info['appname']=namesp[-3]
        info['modelname']=namesp[-1]
    
        # Return the info
        return info

def upload_path(instance, filename):
    '''
    This method is created to return the path to upload files. This path must be 
    different from any other to avoid problems.
    '''
    path_separator = "/"
    date_separator = "-"
    ext_separator = "."
    empty_string = ""
    #get the model name
    model_name = model_inspect(instance)['modelname']
    
    #get the string date
    date = datetime.now().strftime("%Y-%m-%d").split(date_separator)
    curr_day = date[2]
    curr_month = date[1]
    curr_year = date[0]
    
    split_filename = filename.split(ext_separator)
    filename = empty_string.join(split_filename[:-1])
    file_ext = split_filename[-1]
    
    new_filename = empty_string.join([filename,str(random.random()).split(ext_separator)[1]])
    new_filename = ext_separator.join([new_filename,file_ext])
    string_path = path_separator.join([model_name, curr_year, curr_month,curr_day, 
                                       new_filename])
    #the path is built using the current date and the modelname
    return string_path

def get_class(func):
    if not getattr(func, 'func_closure', None):
        return

    for closure in func.func_closure:
        contents = closure.cell_contents

        if not contents:
            continue

        if getattr(contents, '__bases__', None) and issubclass(contents, View):
            return contents

        result = get_class(contents)
        if result:
            return result


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def clean_memcache_item(key, item):
    # clean item from key
    result = cache.get(key)
    if result is not None and item in result:
        result.pop(item)
        cache.set(key, result)


class CodenerixEncoder(object):
    
    codenerix_numeric_dic = {
        'hex36': 'ENWR6MV71JOQHADUGFCYZ25X3B4L0KPTSI98',
        'hex16': '54BEF80D1C96A732',
        'hexz17': 'Z0123456789ABCDEF',
        }
    
    def list_encoders(self):
        return self.codenerix_numeric_dic.keys()
    
    def numeric_encode(self,number,dic='hex36',length=None, cfill='A'):
        
        # Get predefined dictionary
        if dic in self.codenerix_numeric_dic:
            dic = self.codenerix_numeric_dic[dic]
        
        # Find lenght
        ldic=len(dic)
        
        # Initialize
        string=""
        div=ldic+1
        
        # Process number
        while div>=ldic:
            div = number / ldic
            mod = number % ldic
            string+=dic[mod]
            number=div
        
        # If something left behind
        if div:
            string+=dic[div]
        
        # Fill the string if requested
        if length:
            string+=cfill*(length-len(string))
        
        # Return the reverse string
        return string[::-1]
    
    def numeric_decode(self,string,dic='hex36'):
        
        # Get predefined dictionary
        if dic in self.codenerix_numeric_dic:
            dic = self.codenerix_numeric_dic[dic]
        
        # For each character in the string
        first=True
        number=0
        for c in string:
            
            # Not the first loop
            if not first:
                number*=len(dic)
            else:
                first=False
            
            # Attach the character
            number+=dic.index(c)
        
        # Return the final resulting number
        return number


class InMemoryZip(object):
    '''
    # Compress
    imz = InMemoryZip()
    imz.append("info.dat", data).append("test.txt","asdfasfdsaf")
    datazip = imz.read()
    
    # Uncompress
    imz = InMemoryZip(datazip)$
    info_unzipped = imz.get("info.dat")
    '''
    def __init__(self, data=None):
        # Create the in-memory file-like object
        self.in_memory_zip = StringIO.StringIO()
        if data:
            self.in_memory_zip.write(data)
            self.in_memory_zip.seek(0)
    
    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of 
        file_contents to the in-memory zip.'''
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)
        
        # Write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)
        
        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0        
        
        return self
    
    def get(self, filename):
        zf = zipfile.ZipFile(self.in_memory_zip, "r", zipfile.ZIP_DEFLATED, False)
        fp = zf.open(filename)
        data = fp.read()
        return data
    
    def read(self):
        '''Returns a string with the contents of the in-memory zip.'''
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()
    
    def writetofile(self, filename):
        '''Writes the in-memory zip to a file.'''
        f = file(filename, "w")
        f.write(self.read())
        f.close()

