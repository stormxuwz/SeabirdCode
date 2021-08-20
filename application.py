from __future__ import print_function

# ps -fA | grep python
import os
from seabird.seabird_class import seabird
import numpy as np
import pandas as pd
import json,sys
import logging
from sqlalchemy import create_engine

import flask
from flask import Flask, request, redirect, url_for,send_from_directory
from werkzeug.utils import secure_filename

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.models import LinearAxis, Range1d,Span, BoxAnnotation


UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = set(['CNV',"cnv"])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
def getitem(obj, item, default):
    if item not in obj:
        return default
    else:
        return obj[item]

def seabirdAnalysis(filename = None):
    """
    Seabird analysis function, filename is the file of raw CNV data
    """
    # initialize the variables
    args = flask.request.args
    depth_TRM = None
    depth_LEP = None
    depth_UHY = None
    depth_DCL = None
    Prop_DCL = None
    conc_DCL = None
    rightShapeR2 = None
    leftShapeR2 = None
    if filename is not None:
        # print("I have the file"+filename,file=sys.stderr)
        config=json.load(open('./config.json')) # load 
        mySeabird = seabird(config = config)
        
        mySeabird.loadData(dataFile = os.path.join(app.config['UPLOAD_FOLDER'],filename))


        mySeabird.preprocessing()
        mySeabird.identify()

        # plot functions
        fig = figure(title=filename,x_axis_label='Temperature (C)',y_axis_label = "Depth (m)")
        
        fig.line(mySeabird.cleanData.Temperature, -mySeabird.cleanData.Depth, color = "red",legend = "Temperature")
        fig.line(mySeabird.downCastRawData.Temperature, -mySeabird.downCastRawData.Depth, color = "red",line_dash = [5])
        
        fig.extra_x_ranges = {"Fluorescence": Range1d(start=min(mySeabird.cleanData.Fluorescence), end=max(mySeabird.cleanData.Fluorescence))}
        fig.add_layout(LinearAxis(x_range_name="Fluorescence",axis_label = "Fluorescence (ug/L)"), 'below')
        fig.line(mySeabird.cleanData.Fluorescence, -mySeabird.cleanData.Depth, \
                color = "green", x_range_name="Fluorescence",legend = "Fluorescence")
        fig.line(mySeabird.downCastRawData.Fluorescence, -mySeabird.downCastRawData.Depth, \
                color = "green",line_dash = [5],x_range_name = "Fluorescence")

        depth_TRM = mySeabird.features["TRM_segment"]
        depth_LEP = mySeabird.features["LEP_segment"]
        depth_UHY = mySeabird.features["UHY_segment"]


        # depth_TRM = -99 if depth_TRM is None else depth_TRM
        # depth_LEP = -99 if depth_LEP is None else depth_LEP
        # depth_UHY = -99 if depth_UHY is None else depth_UHY
        # depth_DCL = -99 if depth_DCL is None else depth_DCL

        
        if mySeabird.features["DCL_concProp_fit"] is not None:
            depth_DCL = mySeabird.features["DCL_depth"]
            conc_DCL = np.round(mySeabird.features["DCL_conc"]  ,decimals =2)
            rightShapeR2 = np.round(mySeabird.features["DCL_rightShapeFitErr"],decimals=2)
            leftShapeR2 = np.round(mySeabird.features["DCL_leftShapeFitErr"],decimals=2)
            Prop_DCL = np.round(mySeabird.features["DCL_concProp_fit"],decimals=2)
            peak_box = BoxAnnotation(bottom=-mySeabird.features["DCL_bottomDepth_fit"], \
                top=-mySeabird.features["DCL_upperDepth_fit"], fill_alpha=0.1, fill_color='green')
            fig.add_layout(peak_box)
            

            # DCL_upper = Span(location=-mySeabird.features["DCL_upperDepth_fit"], \
                # dimension='width', line_color='green', line_width=3,x_range_name = "Fluorescence",line_dash = [3]) #red line at 0
            # DCL_bottom = Span(location=-mySeabird.features["DCL_bottomDepth_fit"], \
                # dimension='width', line_color='green', line_width=3,x_range_name = "Fluorescence",line_dash = [3]) #red line at 0

        # low_box = BoxAnnotation(top=80, fill_alpha=0.1, fill_color='red')
        # epi_box = BoxAnnotation(bottom = -depth_LEP, fill_alpha = 0.1, fill_color = "yellow")
        # hyp_box = BoxAnnotation(top = -depth_UHY, fill_alpha = 0.1, fill_color = "blue")
        # met_box = BoxAnnotation(top = -depth_UHY, bottom = -depth_LEP, fill_alpha = 0.1, fill_color = "red")

       
        # peak_box2 = BoxAnnotation(bottom=-mySeabird.features["DCL_bottomDepth_gradient"], \
            # top=-mySeabird.features["DCL_upperDepth_gradient"], fill_alpha=0.1, fill_color='red')
        # high_box = BoxAnnotation(bottom=180, fill_alpha=0.1, fill_color='red')
        
        # fig.add_layout(epi_box)
        # fig.add_layout(hyp_box)
        # fig.add_layout(met_box)
        # fig.add_layout(peak_box2)
        DCL = Span(location= 99 if depth_DCL is None else -depth_DCL, \
                dimension='width', line_color='green', line_width=3,x_range_name = "Fluorescence",line_dash = [3]) #red line at 0
        TRM = Span(location= 99 if depth_TRM is None else -depth_TRM, \
            dimension='width', line_color='red', line_width=3,line_dash = [3]) #red line at 0
        LEP = Span(location= 99 if depth_LEP is None else -depth_LEP, \
            dimension='width', line_color='blue', line_width=3,line_dash = [3]) #red line at 0
        UHY = Span(location= 99 if depth_UHY is None else -depth_UHY, \
            dimension='width', line_color='black', line_width=3,line_dash = [3]) #red line at 0
       
        
        fig.renderers.extend([TRM,LEP,UHY,DCL])
        # fig.renderers.extend([TRM,DCL,DCL_bottom,DCL_upper])
        fig.legend.location = "bottom_right"
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    else:
        fig = figure(title="Figures")
 
    # Get all the form arguments in the url with defaults
    # Configure resources to include BokehJS inline in the document.
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/user_guide/embedding.html#components
    script, div = components(fig, INLINE)
    html = flask.render_template(
        'index.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
        depth_TRM = depth_TRM,
        depth_UHY = depth_UHY,
        depth_LEP = depth_LEP,
        depth_DCL = depth_DCL,
        conc_DCL = conc_DCL,
        Prop_DCL = Prop_DCL,
        filename = filename,
        rightShapeR2 = rightShapeR2,
        leftShapeR2 = leftShapeR2
    )
    return html

@app.route('/', methods=['GET', 'POST'])
def index():
    filename = None
    # print(request.method,file=sys.stderr)
    if request.method == 'POST':
        # check if the post request has the file part
 
        if 'file' not in request.files:
            # flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        
        if file.filename == '':
            # flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    else:
        pass

    return seabirdAnalysis(filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



if __name__ == '__main__':
	app.run()