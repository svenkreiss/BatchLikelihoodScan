
all: test

# recipe to create the standard model for tests
tests/standardHistFactory/results/example_combined_GaussExample_model.root:
	cd tests/standardHistFactory; prepareHistFactory
	cd tests/standardHistFactory; hist2workspace config/example.xml

# recipe to create a fake counting model for tests with plugins
tests/twoBin/models/twoBinStandard.root:
	cd tests/twoBin; python twoBinCountingModel.py

# recipe to create a fake counting model for tests with plugins
tests/twoBin/models/twoBinNoNuisParams.root:
	cd tests/twoBin; python twoBinCountingModel.py --noNuisParams --name=twoBinNoNuisParams


test-standardHistFactory: tests/standardHistFactory/results/example_combined_GaussExample_model.root
	@echo "--- Running 1D example shown in README ---"
	cd tests/standardHistFactory; python ../../BatchLikelihoodScan/scan.py --overwritePOI=SigXsecOverSM=1 --overwriteBins=SigXsecOverSM=100 -j 1 -c 0 -q | tee batchProfile.log
	cd tests/standardHistFactory; python ../../BatchLikelihoodScan/plot.py --subtractMinNLL

test-twoBin: tests/twoBin/models/twoBinStandard.root
	@echo "--- Running twoBin test ---"
	cd tests/twoBin; python ../../BatchLikelihoodScan/scan.py -i models/twoBinStandard.root --plugins=BatchLikelihoodScan.Plugins.muTmuW --overwriteBins=muT=50,muW=50 --overwriteRange=muT=[0:3],muW=[0:3] -j 1 -c 0 -q | tee batchProfile.log
	cd tests/twoBin; python ../../BatchLikelihoodScan/plot.py -o PL_data_standard.root --subtractMinNLL
	@echo "The result of the twoBin test is in tests/twoBin/PL_data_standard.root. You can for example look at the scanned nll values in ROOT with profiledNLL->Draw(\"COLZ\")."

test-twoBin-noNuisParams: tests/twoBin/models/twoBinNoNuisParams.root
	@echo "--- Running twoBin test ---"
	cd tests/twoBin; python ../../BatchLikelihoodScan/scan.py -i models/twoBinNoNuisParams.root --plugins=BatchLikelihoodScan.Plugins.muTmuW --overwriteBins=muT=50,muW=50 --overwriteRange=muT=[0:3],muW=[0:3] -j 1 -c 0 -q | tee batchProfile.log
	cd tests/twoBin; python ../../BatchLikelihoodScan/plot.py -o PL_data_noNuisParams.root --subtractMinNLL
	@echo "The result of the twoBin test is in tests/twoBin/PL_data_noNuisParams.root. You can for example look at the scanned nll values in ROOT with profiledNLL->Draw(\"COLZ\")."



test: \
		test-standardHistFactory \
		test-twoBin \
		test-twoBin-noNuisParams
	@echo "Tests done."







# recipe to create the standard model for tests
results/example_combined_GaussExample_model.root:
	prepareHistFactory
	hist2workspace config/example.xml

testInVirtualEnv: results/example_combined_GaussExample_model.root
	@echo "--- Running 1D example shown in README ---"
	batch_likelihood_scan --overwritePOI=SigXsecOverSM=1 --overwriteBins=SigXsecOverSM=100 -j 1 -c 0 -q | tee batchProfile.log
	batch_likelihood_plot --subtractMinNLL
