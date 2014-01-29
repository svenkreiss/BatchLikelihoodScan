#!/usr/bin/env python

""" Created on: April 5, 2013 """

__author__ = "Sven Kreiss, Kyle Cranmer"
__version__ = "0.1"


import time
import ROOT


def preprocess( f,w,mc,data ):
   """ merging production modes mu to (muT,muW) parametrization """

   w.var( "mu" ).setVal( 1.0 )
   w.var( "mu" ).setConstant()

   renameMap = {
      "mu_XS7_ggF": "muT",
      "mu_XS7_ttH": "muT",
      "mu_XS8_ggF": "muT",
      "mu_XS8_ttH": "muT",

      "mu_XS7_VBF": "muW",
      "mu_XS7_WH": "muW",
      "mu_XS7_ZH": "muW",
      "mu_XS8_VBF": "muW",
      "mu_XS8_WH": "muW",
      "mu_XS8_ZH": "muW",
   }   
   
   filteredRenameMap = dict( (k,v) for k,v in renameMap.iteritems() if w.var(k) )
   print( "Renaming: "+str( filteredRenameMap ) )

   # ======== run the actual renaming   
   timeStart = time.time()
   pdfName = mc.GetPdf().GetName()
   
   # This takes fractions of a second:
   for k,v in filteredRenameMap.iteritems(): w.var(k).SetName(v)
   getattr( w,"import" )( mc.GetPdf(), True )
   
   w.var( "muT" ).setConstant( False )
   w.var( "muW" ).setConstant( False )
   mc.SetPdf( w.pdf(pdfName) )
   mc.SetParametersOfInterest( "muT,muW" )
   print( "Time for renaming: %.2fs" % (time.time()-timeStart) )
      
   
   print( "Done renaming for MuTMuW." )
   

