#!/usr/bin/env python

#  BatchProfileLikelihood
# 
#  date: February 12, 2013
# 
#  This is a standard demo that can be used with any ROOT file
#  prepared in the standard way.  You specify:
#  - name for input ROOT file
#  - name of workspace inside ROOT file that holds model and data
#  - name of ModelConfig that specifies details for calculator tools
#  - name of dataset

__author__ = "Sven Kreiss, Kyle Cranmer"
__version__ = "0.1"


import helperModifyModelConfig


import optparse
parser = optparse.OptionParser(version="0.1")
parser.add_option("-o", "--output", help="output location", type="string", dest="output", default="batchOutput/")

helperModifyModelConfig.addOptionsToOptParse( parser )
parser.add_option("-c", "--counter", help="Number of this job.", dest="counter", type="int", default=1)
parser.add_option("-j", "--jobs", help="Number of jobs.", dest="jobs", type="int", default=1)

parser.add_option("-f", "--fullRun", help="Do a full run.", dest="fullRun", default=False, action="store_true")
parser.add_option(      "--unconditionalFitInSeparateJob", help="Do the unconditional fit in a separate job", dest="unconditionalFitInSeparateJob", default=False, action="store_true")
parser.add_option(      "--initVars", help="Set these vars to these values before every fit (to work-around minuit getting stuck in local minima). It takes comma separated inputs of the form var=4.0 or var=4.0+/-1.0 .", dest="initVars", default=None )
parser.add_option(      "--printAllNuisanceParameters", help="Prints all nuisance parameters.", dest="printAllNuisanceParameters", default=False, action="store_true")
parser.add_option(      "--skipOnInvalidNll", help="As the parameter name says.", dest="skipOnInvalidNll", default=False, action="store_true")
parser.add_option(      "--minStrategy", help="Minuit Strategies: 0 fastest, 1 intermediate, 2 slow", dest="minStrategy", default=1, type=int)
parser.add_option(      "--minOptimizeConst", help="NLL optimize const", dest="minOptimizeConst", default=2, type=int)
parser.add_option(      "--reorderParameters", help="Execution order: swap x and y to scan in vertical stripes instead of horizontal. Give index of POIs like 1,0.", dest="reorderParameters", default=False)
parser.add_option(      "--reversedParameters", help="Execution order reversed. Give index of POIs like 0,2.", dest="reversedParameters", default=False)
parser.add_option(      "--enableOffset", help="enable likelihood offsetting", dest="enableOffset", default=False, action="store_true")
parser.add_option(      "--evaluateWithoutOffset", help="evaluate without likelihood offsetting", dest="evaluateWithoutOffset", default=False, action="store_true")

parser.add_option("-q", "--quiet", dest="verbose", action="store_false", default=True, help="Quiet output.")
options,args = parser.parse_args()

import sys
print( ' '.join(sys.argv) )
print( '' )

# to calculate unconditionalFitInSeparateJob, reduce options.jobs by one to make room for the extra job
if options.unconditionalFitInSeparateJob: options.jobs -= 1

if options.reversedParameters: options.reversedParameters = [ int(j) for j in options.reversedParameters.split(",") ]
else:                          options.reversedParameters = []

if options.reorderParameters: options.reorderParameters = [ int(j) for j in options.reorderParameters.split(",") ]
else:                         options.reorderParameters = []



import ROOT
import helperStyle

import PyROOTUtils
import math
from array import array
import time


def setParameterToBin( par, binNumber, reverse = False ):
   if not reverse:
      par.setVal( par.getMin() +  (float(binNumber)+0.5)/par.getBins()*( par.getMax()-par.getMin() ) )
   else:
      par.setVal( par.getMax() -  (float(binNumber)+0.5)/par.getBins()*( par.getMax()-par.getMin() ) )
   
def parametersNCube( parLIn, i, reversedParameters = [], reorderParameters = [] ):
   if parLIn.getSize() == len(reorderParameters):
      parL = ROOT.RooArgList( "reorderedParList" )
      for j in range( parLIn.getSize() ): parL.add( parLIn.at(reorderParameters[j]) )
   else:
      parL = ROOT.RooArgList( parLIn, "reorderedParList" )
   
   for d in reversed( range(parL.getSize()) ):
      if d >= 1:
         lowerDim = reduce( lambda x,y: x*y, [parL.at(dd).getBins() for dd in range(d)] )
         #print( "Par %s: lowerDim=%d, i=%d, i%%lowerDim=%d" % (parL.at(d).GetName(), lowerDim, i, i%lowerDim) )
         setParameterToBin( parL.at(d), int(i/lowerDim) )
         i -= int(i/lowerDim) * lowerDim
      else:
         setParameterToBin( parL.at(d), i, d in reversedParameters )
         
def jobBins( numPoints ):
   if options.unconditionalFitInSeparateJob and options.counter == options.jobs:
      return (0,0)

   return (
      int(math.ceil(float(options.counter)*numPoints/options.jobs)),
      int(math.ceil(float(options.counter+1.0)*numPoints/options.jobs))
   )

def visualizeEnumeration( poiL ):
   if poiL.getSize() != 2:
      print( "ERROR: This is a 2D test." )
      return
   
   numbers = ROOT.TH2F( "binsVis", "visualize bin enumeration;"+poiL.at(0).GetTitle()+";"+poiL.at(1).GetTitle(), 
      poiL.at(0).getBins(), poiL.at(0).getMin(), poiL.at(0).getMax(),
      poiL.at(1).getBins(), poiL.at(1).getMin(), poiL.at(1).getMax(),
   )
   jobs = ROOT.TH2F( "jobsVis", "visualize jobs highlighting job "+str(options.counter)+";"+poiL.at(0).GetTitle()+";"+poiL.at(1).GetTitle(), 
      poiL.at(0).getBins(), poiL.at(0).getMin(), poiL.at(0).getMax(),
      poiL.at(1).getBins(), poiL.at(1).getMin(), poiL.at(1).getMax(),
   )
   jobsMask = ROOT.TH2F( "jobsMask", "visualize jobs highlighting job "+str(options.counter)+";"+poiL.at(0).GetTitle()+";"+poiL.at(1).GetTitle(), 
      poiL.at(0).getBins(), poiL.at(0).getMin(), poiL.at(0).getMax(),
      poiL.at(1).getBins(), poiL.at(1).getMin(), poiL.at(1).getMax(),
   )

   numPoints = reduce( lambda x,y: x*y, [poiL.at(d).getBins() for d in range(poiL.getSize())] )
   for i in range( poiL.at(0).getBins()*poiL.at(1).getBins() ):
      parametersNCube( poiL, i, options.reversedParameters, options.reorderParameters )
      numbers.SetBinContent( numbers.FindBin( poiL.at(0).getVal(), poiL.at(1).getVal() ), i )
      jobs.SetBinContent( jobs.FindBin( poiL.at(0).getVal(), poiL.at(1).getVal() ), int(float(i)/numPoints*options.jobs) )

   firstPoint,lastPoint = jobBins( numPoints )
   for i in range( firstPoint,lastPoint ):
      parametersNCube( poiL, i, options.reversedParameters, options.reorderParameters )
      jobsMask.SetBinContent(
         jobsMask.FindBin( poiL.at(0).getVal(), poiL.at(1).getVal() ),
         1000
      )

   canvas = ROOT.TCanvas( "binEnumeration", "binEnumeration", 800, 400 )
   canvas.SetGrid()
   canvas.Divide(2)
   canvas.cd(1)
   numbers.Draw("COL")
   numbers.Draw("TEXT,SAME")
   canvas.cd(2)
   jobs.Draw("COL")
   jobsMask.Draw("BOX,SAME")
   jobs.Draw("TEXT,SAME")
   canvas.SaveAs( "doc/images/binEnumeration2D.png" )
   canvas.Update()
   raw_input( "Press enter to continue ..." )






def minimize( nll ):
   
   strat = ROOT.Math.MinimizerOptions.DefaultStrategy()

   msglevel = ROOT.RooMsgService.instance().globalKillBelow()
   if not options.verbose:
      ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.FATAL)

   minim = ROOT.RooMinimizer( nll )
   if not options.verbose:
      minim.setPrintLevel(-1)
   else:
      minim.setPrintLevel(1)
   minim.setStrategy(strat)
   minim.optimizeConst(options.minOptimizeConst)

   # Got to be very careful with SCAN. We have to allow for negative mu,
   # so large part of the space that is scanned produces log-eval errors.
   # Therefore, this is usually not feasible.
   #minim.minimize(ROOT.Math.MinimizerOptions.DefaultMinimizerType(), "Scan")
   
   status = -1
   for i in range( 3 ):
      status = minim.minimize(ROOT.Math.MinimizerOptions.DefaultMinimizerType(), 
                              ROOT.Math.MinimizerOptions.DefaultMinimizerAlgo())
      if status == 0: break

      if status != 0  and  status != 1  and  strat <= 1:
         strat += 1
         print( "Retrying with strat "+str(strat) )
         minim.setStrategy(strat)
         status = minim.minimize(ROOT.Math.MinimizerOptions.DefaultMinimizerType(), 
                                 ROOT.Math.MinimizerOptions.DefaultMinimizerAlgo())
      
      if status != 0  and  status != 1  and  strat <= 1:
         strat += 1
         print( "Retrying with strat "+str(strat) )
         minim.setStrategy(strat)
         status = minim.minimize(ROOT.Math.MinimizerOptions.DefaultMinimizerType(), 
                                 ROOT.Math.MinimizerOptions.DefaultMinimizerAlgo())
      
   if status != 0 and status != 1:
      print( "ERROR::Minimization failed!" )

   ROOT.RooMsgService.instance().setGlobalKillBelow(msglevel)
   return nll.getVal()



def preFit( w, mc, nll ):   
   if not options.initVars: return
   
   initVars = helperModifyModelConfig.varsDictFromString( options.initVars )
   for name,valErr in initVars.iteritems():
      if w.var( name ):
         if valErr[1]:
            print( "PREFIT - INITVARS: "+name+" = "+str(valErr[0])+" +/- "+str(valErr[1]) )
            w.var( name ).setVal( valErr[0] )
            w.var( name ).setError( valErr[1] )
         else:
            print( "PREFIT - INITVARS: "+name+" = "+str(valErr[0])+" (not setting error)" )
            w.var( name ).setVal( valErr[0] )
      else:
         print( "WARNING PREFIT - INITVARS: "+name+" not in workspace." )



def main():
   if options.verbose:
      print( "Given options: " )
      print( options )
   timeStart = time.time()

   ROOT.RooRandom.randomGenerator().SetSeed( 0 )

   f = ROOT.TFile.Open( options.input )
   w = f.Get( options.wsName )
   mc = w.obj( options.mcName )
   data = w.data( options.dataName )
   
   f,w,mc,data = helperModifyModelConfig.apply( options, f,w,mc,data )

   if options.verbose:
      print( "--- main pdf to use ---" )
      print( mc.GetPdf() )
      print( mc.GetPdf().GetName() )
      print( mc.GetPdf().ClassName() )
      print( "" )
      print( "--- data to use ---" )
      print( data )
      print( data.GetName() )
      print( data.ClassName() )
      print( "" )

   firstPOI = mc.GetParametersOfInterest().first()
   poiL = ROOT.RooArgList( mc.GetParametersOfInterest() )
   nuisL = ROOT.RooArgList( mc.GetNuisanceParameters() )

   if options.fullRun: visualizeEnumeration( poiL )



   ##### Script starts here

   if not options.verbose:
      ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.FATAL)
   
   ROOT.RooAbsReal.defaultIntegratorConfig().method1D().setLabel("RooAdaptiveGaussKronrodIntegrator1D")

   ROOT.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2","Minimize")
   ROOT.Math.MinimizerOptions.SetDefaultStrategy(options.minStrategy)
   #ROOT.Math.MinimizerOptions.SetDefaultPrintLevel(1)
   ROOT.Math.MinimizerOptions.SetDefaultPrintLevel(-1)
   #ROOT.Math.MinimizerOptions.SetDefaultTolerance(0.0001)

   params = mc.GetPdf().getParameters(data)
   ROOT.RooStats.RemoveConstantParameters(params)
   nll = mc.GetPdf().createNLL(
      data, 
      ROOT.RooFit.CloneData(ROOT.kFALSE), 
      ROOT.RooFit.Constrain(params), 
      ROOT.RooFit.GlobalObservables(mc.GetGlobalObservables()),
      ROOT.RooFit.Offset(options.enableOffset),
   )
   nll.setEvalErrorLoggingMode(ROOT.RooAbsReal.CountErrors)
   if options.evaluateWithoutOffset:
      nllNoOffset = mc.GetPdf().createNLL(
         data, 
         ROOT.RooFit.CloneData(ROOT.kFALSE), 
         ROOT.RooFit.Constrain(params), 
         ROOT.RooFit.GlobalObservables(mc.GetGlobalObservables()),
         ROOT.RooFit.Offset(False),
      )
      nllNoOffset.setEvalErrorLoggingMode(ROOT.RooAbsReal.CountErrors)
   if options.enableOffset:
      print( "Get NLL once. This first call sets the offset, so it is important that this happens when the parameters are at their initial values." )
      print( "nll = "+str( nll.getVal() ) )


      
   numPoints = reduce( lambda x,y: x*y, [poiL.at(d).getBins() for d in range(poiL.getSize())] )
   firstPoint,lastPoint = jobBins( numPoints )
   print( "" )
   print( "### Batch Job" )
   print( "* Total grid points: "+str(numPoints) )
   jobsString = str(options.jobs)
   if options.unconditionalFitInSeparateJob: jobsString += " +1 for unconditional fit"
   else: jobsString += " (unconditional fit done in each job)"
   print( "* Total number of jobs: "+jobsString )
   print( "* This job number: "+str(options.counter) )
   print( "* Processing these grid points: [%d,%d)" % (firstPoint,lastPoint) )
   print( "" )

   # for later plotting, print some book-keeping info
   print( "### Parameters Of Interest" )
   for p in range( poiL.getSize() ):
      print( "* POI "+ ("%s=[%d,%f,%f]" % (poiL.at(p).GetName(),poiL.at(p).getBins(),poiL.at(p).getMin(),poiL.at(p).getMax())) )
   print( "" )

   # if all nuisance parameters are requested, also print their book-keeping info here
   if options.printAllNuisanceParameters:
      print( "### Nuisance Parameters" )
      for p in range( nuisL.getSize() ):
         print( "* NUIS "+ ("%s=[%d,%f,%f]" % (nuisL.at(p).GetName(),nuisL.at(p).getBins(),nuisL.at(p).getMin(),nuisL.at(p).getMax())) )
      print( "" )
      print( "" )


   # unconditional fit
   if (not options.unconditionalFitInSeparateJob) or \
      (options.unconditionalFitInSeparateJob and options.counter == options.jobs):
      preFit( w, mc, nll )
      for p in range( poiL.getSize() ): poiL.at(p).setConstant(False)
      print( "" )
      print( "--- unconditional fit ---" )
      minimize( nll )
      nllVal = None
      if options.evaluateWithoutOffset: nllVal = nllNoOffset.getVal()
      else:                             nllVal = nll.getVal()

      # build result line
      result = "ucmles -- nll="+str(nllVal)+", "
      # poi values
      result += ", ".join( [poiL.at(p).GetName()+"="+str(poiL.at(p).getVal()) for p in range(poiL.getSize())] )
      # nuisance parameter values if requested
      if options.printAllNuisanceParameters:
         result += ", "
         result += ", ".join( [nuisL.at(p).GetName()+"="+str(nuisL.at(p).getVal()) for p in range(nuisL.getSize())] )
      print( result )

      f,w,mc,data = helperModifyModelConfig.callHooks( options, f,w,mc,data, type="postUnconditionalFit" )


   # conditional fits
   for p in range( poiL.getSize() ): poiL.at(p).setConstant()
   for i in range( firstPoint,lastPoint ):
      preFit( w, mc, nll )
      parametersNCube( poiL, i, options.reversedParameters, options.reorderParameters )
      print( "" )
      print( "--- next point: "+str(i)+" ---" )
      print( "Parameters Of Interest: "+str([ poiL.at(p).getVal() for p in range(poiL.getSize()) ]) )
      f,w,mc,data = helperModifyModelConfig.callHooks( options, f,w,mc,data, type="preConditionalFit" )
      nllVal = None
      if options.evaluateWithoutOffset: nllVal = nllNoOffset.getVal()
      else:                             nllVal = nll.getVal()
      if options.skipOnInvalidNll and (nllVal > 1e30  or  nllVal != nllVal):
         print( "WARNING: nll value invalid. Skipping minimization was requested." )
      else:
         minimize( nll )
         if options.evaluateWithoutOffset: nllVal = nllNoOffset.getVal()
         else:                             nllVal = nll.getVal()
      
      # build result line
      result = "nll="+str(nllVal)+", "
      # poi values
      result += ", ".join( [poiL.at(p).GetName()+"="+str(poiL.at(p).getVal()) for p in range(poiL.getSize())] )
      # nuisance parameter values if requested
      if options.printAllNuisanceParameters:
         result += ", "
         result += ", ".join( [nuisL.at(p).GetName()+"="+str(nuisL.at(p).getVal()) for p in range(nuisL.getSize())] )
      print( result )
      
   print( "\nDone. Time=%.1fs." % (time.time()-timeStart) )
      


if __name__ == "__main__":
   main()
