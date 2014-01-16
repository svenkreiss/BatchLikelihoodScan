
# recipe to create the standard model for tests
results/example_combined_GaussExample_model.root:
	prepareHistFactory
	hist2workspace config/example.xml

test: results/example_combined_GaussExample_model.root
	@echo "--- Running 1D example shown in README ---"
	batch_likelihood_scan --overwritePOI=SigXsecOverSM=1 --overwriteBins=SigXsecOverSM=100 -j 1 -c 0 -q | tee batchProfile.log
	batch_likelihood_plot --subtractMinNLL
