#!/usr/bin/env python

""" Created on: March 29, 2013 """

__author__ = "Sven Kreiss, Kyle Cranmer"
__version__ = "0.1"



def preprocess( f,w,mc,data ):
   """ This is an example. """
   
   print( "This is the example plugin inside the preprocess() function." )
   print( "The name of the pdf in the ModelConfig is: "+str( mc.GetPdf().GetName() ) )
      

