#!/usr/bin/env python

#  Created on: February 12, 2013

__author__ = "Sven Kreiss, Kyle Cranmer"
__version__ = "0.1"




import optparse

parser = optparse.OptionParser(version="0.1")
parser.add_option("-i", "--inputFiles", help="glob expression for log files from BatchProfileLikelihood.py", type="string", dest="inputFiles", default="batchProfile.log")
parser.add_option("-o", "--outputFile", help="output root file", type="string", dest="outputFile", default="PL_data.root")
parser.add_option(      "--subtractMinNLL", help="subtracts the minNLL", dest="subtractMinNLL", default=False, action="store_true")
parser.add_option("-q", "--quiet", dest="verbose", action="store_false", default=True, help="Quiet output.")
(options, args) = parser.parse_args()

import ROOT
ROOT.gROOT.SetBatch( True )
import PyROOTUtils

import os, math
import glob, re
from array import array



def getContours( hist, level, levelName, canvas ):
   hist.SetContour( 1, array('d',[level]) )
   hist.Draw( "CONT LIST" )
   canvas.Update()
   listOfGraphs = ROOT.gROOT.GetListOfSpecials().FindObject("contours").At(0)
   contours = [ ROOT.TGraph( listOfGraphs.At(i) ) for i in range( listOfGraphs.GetSize() ) ]
   for co in range( len(contours) ):
      contours[co].SetLineWidth( 2 )
      contours[co].SetLineColor( ROOT.kBlue )
      contours[co].SetName( "Contour%s_%d" % (levelName,co) )
   return contours




def getInputFromLogs( files ):
   files = glob.glob( options.inputFiles )
   print( "Files: "+str(files) )
   
   bestFit = {}
   NLL = {'nll':[]}
   POIs = []
   NUISs = []
   
   regexParValue = re.compile( "^(?P<par>[-\b\w\d_\.]+)=(?P<value>[-\d\.einf]+)$" )
   
   for fName in files:
      print( "Opening "+fName )
      f = open( fName )
      for l in f:
         if l[:6] == "* POI ":
            poiName = l[6:l.find("=")]
            poiConfig = l[l.find("=")+2:-2]
            poiConfig = [ float(p) for p in poiConfig.split(",") ]
            if poiName not in [p[0] for p in POIs]:
               POIs.append( (poiName, poiConfig) )
               NLL[ poiName ] = []
         if l[:7] == "* NUIS ":
            nuisName = l[7:l.find("=")]
            nuisConfig = l[l.find("=")+2:-2]
            nuisConfig = [ float(p) for p in nuisConfig.split(",") ]
            if nuisName not in [p[0] for p in NUISs]:
               NUISs.append( (nuisName, nuisConfig) )
               NLL[ nuisName ] = []
               
         if l[:4] == "nll=":
            pars = {}
            parAndValues = l.split(", ")
            for pv in parAndValues:
               regm = regexParValue.match( pv )
               if regm:
                  try:
                     pars[ regm.groupdict()['par'] ] = float(regm.groupdict()['value'])
                  except ValueError:
                     print( "WARNING could not convert value to float." )
            
            if len( pars.keys() ) == len( NLL.keys() ):
               for p,v in pars.iteritems():
                  NLL[ p ].append( v )
            else:
               print( "WARNING: Did not find all parameters. Not adding values. line: "+l )

         if l[:14] == "ucmles -- nll=":
            pars = {}
            parAndValues = l.split(", ")
            for pv in parAndValues:
               regm = regexParValue.match( pv )
               if regm:
                  try:
                     pars[ regm.groupdict()['par'] ] = float(regm.groupdict()['value'])
                  except ValueError:
                     print( "WARNING could not convert value to float." )
            
            if len( pars.keys() ) == len( POIs )+len( NUISs ):
               for p,v in pars.iteritems():
                  if p == "ucmles -- nll": p = "nll"
                  bestFit[ p ] = v
            else:
               print( "WARNING: Did not find all parameters. Not adding values. line: "+l )

      f.close()
      
   return (POIs,NUISs,NLL,bestFit)


def main():
   POIs,NUISs,NLL,bestFit = getInputFromLogs( options.inputFiles )

   print( "\n--- POIs ---" )
   print( POIs )

   print( "\n--- Best fit ---" )
   print( [ (name,value) for name,value in bestFit.iteritems() if name in [p[0] for p in POIs] or name == 'nll' ] )

   print( "\n--- NLL ---" )
   maxNLL = max( [n for n in NLL['nll'] if n < 1e10] )
   if "nll" in bestFit:
      minNLL = bestFit["nll"]
   else:
      minNLL = min( [n for n in NLL['nll']] )
   for i in range( len(NLL['nll']) ):
      if NLL['nll'][i] < minNLL: NLL['nll'][i] = minNLL
      if NLL['nll'][i] > maxNLL: NLL['nll'][i] = maxNLL
   print( "(minNLL,maxNLL) = (%f,%f)" % (minNLL,maxNLL) )


   bestFitMarker = None
   if len( POIs ) == 1  and  POIs[0][0] in bestFit:
      bestFitMarker = ROOT.TMarker( bestFit[ POIs[0][0] ], 0.0, 2 )
   elif len( POIs ) >= 2  and  POIs[0][0] in bestFit  and  POIs[1][0] in bestFit:
      bestFitMarker = ROOT.TMarker( bestFit[ POIs[0][0] ], bestFit[ POIs[1][0] ], 2 )
      


   nllHist = None
   nuisHists = []
   tgs = []
   maxHist = maxNLL
   if options.subtractMinNLL: maxHist -= minNLL
   if len( POIs ) == 1:
      poi = POIs[0]
      nllHist = ROOT.TH1D( "profiledNLL", "profiled NLL;"+poi[0]+";NLL", int(poi[1][0]), poi[1][1], poi[1][2] )
      
      # initialize to maxNLL
      for i in range( nllHist.GetNbinsX()+2 ): nllHist.SetBinContent( i, maxHist )

      for nll,p in zip(NLL['nll'],NLL[poi[0]]):
         bin,val = (None,None)
         bin = nllHist.FindBin( p )
         val = nll
         if options.subtractMinNLL: val -= minNLL
         if nllHist.GetBinContent( bin ) > val: nllHist.SetBinContent( bin, val )
   if len( POIs ) == 2:
      poi1 = POIs[0]
      poi2 = POIs[1]
      nllHist = ROOT.TH2D( 
         "profiledNLL", "profiled NLL;"+poi1[0]+";"+poi2[0]+";NLL",
         int(poi1[1][0]), poi1[1][1], poi1[1][2],
         int(poi2[1][0]), poi2[1][1], poi2[1][2],
      )
      
      # initialize to maxNLL
      for i in range( (nllHist.GetNbinsX()+2)*(nllHist.GetNbinsY()+2) ): nllHist.SetBinContent( i, maxHist )

      for nll,p1,p2 in zip(NLL['nll'],NLL[poi1[0]],NLL[poi2[0]]):
         bin,val = (None,None)
         bin = nllHist.FindBin( p1,p2 )
         val = nll
         if options.subtractMinNLL: val -= minNLL
         if nllHist.GetBinContent( bin ) > val: nllHist.SetBinContent( bin, val )
         
      # in 2D, also create 68% and 95% contours
      c = ROOT.TCanvas()
      tgs += getContours( nllHist, 1.15, "68TG", c )
      tgs += getContours( nllHist, 3.0,  "95TG", c )

      # store the nuisance parameter values
      nuisHists = []
      for n in NUISs:
         h = ROOT.TH2D(
            "nuisParValue_"+n[0], "value of "+n[0]+";"+poi1[0]+";"+poi2[0]+";nuisance parameter value",
            int(poi1[1][0]), poi1[1][1], poi1[1][2],
            int(poi2[1][0]), poi2[1][1], poi2[1][2],
         )
         for nVal,p1,p2 in zip(NLL[n[0]],NLL[poi1[0]],NLL[poi2[0]]):
            bin = nllHist.FindBin( p1,p2 )
            h.SetBinContent( bin, nVal )
         nuisHists.append( h )

   if len( POIs ) == 3:
      poi1 = POIs[0]
      poi2 = POIs[1]
      poi3 = POIs[2]
      nllHist = ROOT.TH3D( 
         "profiledNLL", "profiled NLL;"+poi1[0]+";"+poi2[0]+";"+poi3[0],
         int(poi1[1][0]), poi1[1][1], poi1[1][2],
         int(poi2[1][0]), poi2[1][1], poi2[1][2],
         int(poi3[1][0]), poi3[1][1], poi3[1][2],
      )
      
      # initialize to maxNLL
      for i in range( (nllHist.GetNbinsX()+2)*(nllHist.GetNbinsY()+2)*(nllHist.GetNbinsZ()+2) ): 
         nllHist.SetBinContent( i, maxHist )

      for nll,p1,p2,p3 in zip(NLL['nll'],NLL[poi1[0]],NLL[poi2[0]],NLL[poi3[0]]):
         bin,val = (None,None)
         bin = nllHist.FindBin( p1,p2,p3 )
         val = nll
         if options.subtractMinNLL: val -= minNLL
         if nllHist.GetBinContent( bin ) > val: nllHist.SetBinContent( bin, val )
         
      # # in 2D, also create 68% and 95% contours
      # c = ROOT.TCanvas()
      # tgs += getContours( nllHist, 1.15, "68TG", c )
      # tgs += getContours( nllHist, 3.0,  "95TG", c )


      
   if not nllHist:
      print( "ERROR: Couldn't create nll histogram." )
      return
   
      
   # 2d debug histos
   histos2d = {}
   # change the names below for your model
   params2d = [(POIs[0][0],"nuis1","nuis2"),(POIs[0][0],"nuis1","nuis3")]
   for poi,nuis1,nuis2 in params2d:
      nu1 = [ n for n in NUISs if nuis1==n[0] ]
      nu2 = [ n for n in NUISs if nuis2==n[0] ]
      if len( nu1 ) != 1   or   len( nu2 ) != 1: continue
      nu1 = nu1[0]
      nu2 = nu2[0]
      h = ROOT.TH2D( 
         poi+"_"+nuis1+"_"+nuis2, poi+"_"+nuis1+"_"+nuis2, 
         int(nu1[1][0]), nu1[1][1], nu1[1][2],
         int(nu2[1][0]), nu2[1][1], nu2[1][2],
      )
      for poiVal,n1,n2 in zip( NLL[poi], NLL[nuis1], NLL[nuis2] ):
         h.SetBinContent( h.FindBin( n1,n2 ), poiVal )
      histos2d[ h.GetName() ] = h

   # create tgraphs
   nllTGraphs = {}
   nuisParGraphs = {}
   for poi in POIs:
      xDict = {}
      for x,n in zip( NLL[poi[0]], NLL['nll'] ):
         if x in xDict: xDict[x].append( n )
         else:          xDict[x] = [ n ]
      # profile in unseen poi directions
      nllTGraph = PyROOTUtils.Graph( [(x,min(y)) for x,y in xDict.iteritems()] )
      if options.subtractMinNLL: nllTGraph.add( -minNLL )
      nllTGraphs[poi[0]] = nllTGraph
      

      for nuis in NUISs:
         xA = NLL[ poi[0] ]
         if poi[0] != POIs[0][0]: xOtherA = NLL[ POIs[0][0] ]
         elif len( POIs ) > 1:    xOtherA = NLL[ POIs[1][0] ]
         else:                    xOtherA = NLL[ POIs[0][0] ]  # just a place holder
         yA = NLL[ nuis[0] ]
         nllA = NLL[ 'nll' ]
         
         xDict = {}
         for x,xOther,y,n in zip(xA,xOtherA,yA,nllA):
            if x in xDict: xDict[x].append( (n,y,xOther) )
            else:          xDict[x] = [ (n,y,xOther) ]

         xAMin      = [ x          for x,ny in xDict.iteritems() ]
         yAMin      = [ min(ny)[1] for x,ny in xDict.iteritems() ]
         nuisParGraphs[ poi[0]+"_vs_"+nuis[0] ] = PyROOTUtils.Graph( xAMin, yAMin, nameTitle="nuisPar_"+poi[0]+"_vs_"+nuis[0] )

         if len( POIs ) > 1:
            # profile in unseen poi directions
            #    Create an xOther to distinguish whether this point is in the
            #    +1sigma or -1sigma contour. In cases where y is not convex,
            #    this will still create a correct line when the likelihood is
            #    convex in the POI space.
            #    Ie lines where the 2sigma line dips below the 1sigma line and
            #    even crosses it are correct and using this are also drawn correctly.
            xOtherAMin = [ min(ny)[2] for x,ny in xDict.iteritems() ]

            # var values at contours:
            thresholds = [2.3/2.0, 6.0/2.0]  # 2d: 68% and 95%
            for t in thresholds:
               xyPos = []
               xyNeg = []
               for x,ny,xOtherMin in zip( xDict.keys(),xDict.values(),xOtherAMin ):
                  # skip if the smallest nll is not below the threshold
                  if min(ny)[0] > minNLL+t: continue
            
                  # build a list of y values larger than ymin and find the value closest to the threshold
                  nySlice = [ (math.fabs(n-minNLL-t),y) for n,y,xOther in ny if xOther > xOtherMin ]
                  if nySlice: xyPos.append( (x,min(nySlice)[1]) )
                  # build a list of y values less than ymin and find the value closest to the threshold
                  nySlice = [ (math.fabs(n-minNLL-t),y) for n,y,xOther in ny if xOther < xOtherMin ]
                  if nySlice: xyNeg.append( (x,min(nySlice)[1]) )
               
               if xyPos: nuisParGraphs[ poi[0]+"_vs_"+nuis[0]+"_thresholdPos_"+str(t) ] = PyROOTUtils.Graph( xyPos )
               if xyNeg: nuisParGraphs[ poi[0]+"_vs_"+nuis[0]+"_thresholdNeg_"+str(t) ] = PyROOTUtils.Graph( xyNeg )
            
            # make a histogram
            nllHistNuisPoi = ROOT.TH2D( 
               "nuisPar_"+poi[0]+"_vs_"+nuis[0]+"_nllHist", 
               "profiled NLL;"+poi[0]+";"+nuis[0]+";NLL",
               int(poi[1][0]), poi[1][1], poi[1][2],
               int(nuis[1][0]), min(yA), max(yA),
            )
            for x,y,n in zip( NLL[ poi[0] ], NLL[ nuis[0] ], NLL[ 'nll' ] ):
               b = nllHistNuisPoi.FindBin( x,y )
               if nllHistNuisPoi.GetBinContent( b ) == 0.0  or  nllHistNuisPoi.GetBinContent( b ) > n-minNLL:
                  nllHistNuisPoi.SetBinContent( b,n-minNLL )
            nuisParGraphs[ poi[0]+"_vs_"+nuis[0]+"_nllHist" ] = nllHistNuisPoi
         
            # add best fit marker in this plane
            if poi[0] in bestFit and nuis[0] in bestFit:
               nuisParGraphs[ poi[0]+"_vs_"+nuis[0]+"_bestFit" ] = ROOT.TMarker( bestFit[ poi[0] ], bestFit[ nuis[0] ], 2 )
         
               
   
   
   print( "Writing file: "+options.outputFile )
   f = ROOT.TFile( options.outputFile, "RECREATE" )
   nllHist.Write()
   for p,g in nllTGraphs.iteritems():
      if g: g.Write( "nll_"+p )
   for h in nuisHists:
      h.Write()
   for p,g in nuisParGraphs.iteritems():
      if g: g.Write( "nuisPar_"+p )
   for h in histos2d.values():
      h.Write()
   for tg in tgs:
      tg.Write()
   if bestFitMarker: bestFitMarker.Write("bestFit")
   f.Close()
   
   if options.verbose:
      import helperStyle
      canvas = ROOT.TCanvas( "verboseOutput", "verbose output", 600,300 )
      canvas.Divide( 2 )
      canvas.cd(1)
      nllHist.SetLineWidth( 2 )
      nllHist.SetLineColor( ROOT.kBlue )
      nllHist.Draw("HIST")
      if nllTGraph: 
         nllTGraph.SetLineWidth( 2 )
         nllTGraph.SetLineColor( ROOT.kRed )
         nllTGraph.Draw("SAME")

         canvas.cd(2)
         lGraph = PyROOTUtils.Graph( nllTGraph )
         lGraph.SetTitle( "Likelihood" )
         lGraph.transformY( lambda y: math.exp(-y) )
         lGraph.Draw("AXIS L")
      canvas.SaveAs( "doc/images/batchProfileLikelihood1D.png" )
      canvas.Update()
      raw_input( "Press enter to continue ..." )
   

   
   
if __name__ == "__main__":
   main()