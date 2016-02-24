import sys
import os
import shutil 
import re
from pyspark import SparkContext
from pyspark.mllib.clustering import KMeans
from pyspark.mllib.evaluation import MulticlassMetrics
from pyspark.mllib.classification import LogisticRegressionWithLBFGS, NaiveBayes, NaiveBayesModel
from pyspark.mllib.util import MLUtils
from pyspark.mllib.linalg import Vectors
from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel, Rating
from pyspark.mllib.regression import LabeledPoint, LinearRegressionWithSGD, LinearRegressionModel
from pyspark.mllib.tree import RandomForest, RandomForestModel
from pyspark.sql import SQLContext
from pyspark.sql import DataFrame
from numpy import array
import math
from pyspark.mllib.regression import IsotonicRegression, IsotonicRegressionModel
import subprocess

# Evaluate clustering by computing Within Set Sum of Squared Errors
def error(point):
    center = clusters.centers[clusters.predict(point)]
    return sqrt(sum([x**2 for x in (point - center)]))

#"/Users/jacobliu/HoneyPySpark/spark-1.5.2-bin-hadoop2.6/README.md"  # Should be some file on your system
sc = SparkContext("local", "PySpark")
SQLContext = SQLContext(sc)

def main():
	loadTrainingFilePath = sys.argv[1]		#tainning file path
	#loadTestingFilePath = sys.argv[2]		#testing file path
	#dumpFilePath = sys.argv[3]				#output file path
	hdfsFilePath = "/user/honeycomb/sparkteam/output"
	model_name = sys.argv[2]   #"Regression"				#model_name

	print sys.argv[1]

	##test##
	#readLocalFile("/Users/jacobliu/SparkService/data/sample_libsvm_data.txt")

	#if the directory already exists, delete it
	#ifExisted = subprocess.call(["hdfs","dfs","-test","-d",hdfsFilePath])
	#if ifExisted == 0:
	#	subprocess.call(["hdfs","dfs","-rm","-r", hdfsFilePath])
	#if os.path.exists(dumpFilePath):
		#shutil.rmtree(dumpFilePath)
		#hdfs.delete_file_dir(dumpFilePath)
		
	if model_name == "LinearRegression":
		LinearRegression(loadTrainingFilePath)

	elif model_name == "IsotonicRegression":
		Isotonic_Regression(loadTrainingFilePath)

	elif model_name == "ALS":
		Alternating_Least_Squares(loadTrainingFilePath)

	elif model_name == "NaiveBayes":
		Naive_Bayes(loadTrainingFilePath)

	elif model_name == "RandomForest":
		Random_Forest(loadTrainingFilePath)
		
	elif model_name == "KMeans":
		# Load and parse the data
		data = sc.textFile(loadTrainingFilePath)
		parsedData = data.map(lambda line: array([float(x) for x in line.split(' ')]))
		# Build the model (cluster the data)
		clusters = KMeans.train(parsedData, 3, maxIterations=10, runs=30, initializationMode="random")

		WSSSE = parsedData.map(lambda point: error(point)).reduce(lambda x, y: x + y)
		
		print("Within Set Sum of Squared Error = " + str(WSSSE))
		
		#write to file as JSON
		#res = [('k_means',dumpFilePath, WSSSE)]
		#rdd = sc.parallelize(res)
		#SQLContext.createDataFrame(rdd).collect()
		#df = SQLContext.createDataFrame(rdd,['model_name','res_path', 'WSSSE'])
		#df.toJSON().saveAsTextFile(dumpFilePath)

	elif model_name == "LogisticRegression":
		# Load training data in LIBSVM format
		data = MLUtils.loadLibSVMFile(sc, loadTrainingFilePath)
		
		
		# Split data into training (60%) and test (40%)
		traindata, testdata = data.randomSplit([0.6, 0.4], seed = 11L)
		traindata.cache()

		# Load testing data in LIBSVM format
		#testdata = MLUtils.loadLibSVMFile(sc, loadTestingFilePath)

		# Run training algorithm to build the model
		model = LogisticRegressionWithLBFGS.train(traindata, numClasses=3)

		# Compute raw scores on the test set
		predictionAndLabels = testdata.map(lambda lp: (float(model.predict(lp.features)), lp.label))

		# Instantiate metrics object
		metrics = MulticlassMetrics(predictionAndLabels)

		# Overall statistics
		precision = metrics.precision()
		recall = metrics.recall()
		f1Score = metrics.fMeasure()
		#confusion_matrix = metrics.confusionMatrix().toArray()

		print("Summary Stats")
		print("Precision = %s" % precision)
		print("Recall = %s" % recall)
		print("F1 Score = %s" % f1Score)


		# Statistics by class
		labels = traindata.map(lambda lp: lp.label).distinct().collect()
		for label in sorted(labels):
		    print("Class %s precision = %s" % (label, metrics.precision(label)))
		    print("Class %s recall = %s" % (label, metrics.recall(label)))
		    print("Class %s F1 Measure = %s" % (label, metrics.fMeasure(label, beta=1.0)))

		# Weighted stats
		print("Weighted recall = %s" % metrics.weightedRecall)
		print("Weighted precision = %s" % metrics.weightedPrecision)
		print("Weighted F(1) Score = %s" % metrics.weightedFMeasure())
		print("Weighted F(0.5) Score = %s" % metrics.weightedFMeasure(beta=0.5))
		print("Weighted false positive rate = %s" % metrics.weightedFalsePositiveRate)

		#return model parameters
		res = [('1','Yes','TP Rate', metrics.truePositiveRate(0.0)),
			   ('2','Yes','FP Rate', metrics.falsePositiveRate(0.0)),
			   ('3','Yes','Precision', metrics.precision(0.0)),
			   ('4','Yes','Recall', metrics.recall(0.0)),
		       ('5','Yes','F-Measure', metrics.fMeasure(0.0, beta=1.0)),
		       ('1','Yes','TP Rate', metrics.truePositiveRate(1.0)),
			   ('2','Yes','FP Rate', metrics.falsePositiveRate(1.0)),
		       ('3','Yes','Precision', metrics.precision(1.0)),
			   ('4','Yes','Recall', metrics.recall(1.0)),
		       ('5','Yes','F-Measure', metrics.fMeasure(1.0, beta=1.0)),
		       ('1','Yes','TP Rate', metrics.truePositiveRate(2.0)),
			   ('2','Yes','FP Rate', metrics.falsePositiveRate(2.0)),
		       ('3','Yes','Precision', metrics.precision(2.0)),
		       ('4','Yes','Recall', metrics.recall(2.0)),
		       ('5','Yes','F-Measure', metrics.fMeasure(2.0, beta=1.0))]	

		#save output file path as JSON and dump into dumpFilePath
		rdd = sc.parallelize(res)
		SQLContext.createDataFrame(rdd).collect()
		df = SQLContext.createDataFrame(rdd,['Order','CLass','Name', 'Value'])

		#tempDumpFilePath = dumpFilePath + "/part-00000"
		#if os.path.exists(tempDumpFilePath):
		#	os.remove(tempDumpFilePath)

		#df.toJSON().saveAsTextFile(hdfsFilePath)
		#tmpHdfsFilePath = hdfsFilePath + "/part-00000"
		#subprocess.call(["hadoop","fs","-copyToLocal", tmpHdfsFilePath, dumpFilePath])

		# Save and load model
		#clusters.save(sc, "myModel")
		#sameModel = KMeansModel.load(sc, "myModel")

#Read from local file, sample test read a txt file and output the columns
def readLocalFile(filename):
	with open(filename, 'r') as f:
		for line in f.readlines():
			for words in line.strip().split(" "):
				print words


# Load and parse the data
def parsePoint(line):
    values = [float(x) for x in line.replace(',', ' ').split(' ')]
    return LabeledPoint(values[0], values[1:])

def LinearRegression(filename):
	data = sc.textFile(filename)
	parsedData = data.map(parsePoint)

	# train the model
	model = LinearRegressionWithSGD.train(parsedData)

	# Evaluate the model on training data
	valuesAndPreds = parsedData.map(lambda p: (p.label, model.predict(p.features)))
	MSE = valuesAndPreds.map(lambda (v, p): (v - p)**2).reduce(lambda x, y: x + y) / valuesAndPreds.count()
	print("\n\n\n\n\n\nMean Squared Error = " + str(MSE) + "\n\n\n\n\n")

	# Save and load model
	#model.save(sc, "myModelPath")
	#sameModel = LinearRegressionModel.load(sc, "myModelPath")

# Naive Bayes helper function:
def parseLine(line):
    parts = line.split(',')
    label = float(parts[0])
    features = Vectors.dense([float(x) for x in parts[1].split(' ')])
    return LabeledPoint(label, features)


def Naive_Bayes(filename):
	data = sc.textFile(filename).map(parseLine)

	# Split data aproximately into training (60%) and test (40%)
	training, test = data.randomSplit([0.6, 0.4], seed=0)

	# Train a naive Bayes model.
	model = NaiveBayes.train(training, 1.0)

	# Make prediction and test accuracy.
	predictionAndLabel = test.map(lambda p: (model.predict(p.features), p.label))
	accuracy = 1.0 * predictionAndLabel.filter(lambda (x, v): x == v).count() / test.count()

	# Output the results:
	print "***************************************"
	print 'Accuracy =' + str(accuracy)
	print "***************************************"

	# Save and load model
	#model.save(sc, "target/tmp/myNaiveBayesModel")
	#sameModel = NaiveBayesModel.load(sc, "target/tmp/myNaiveBayesModel")

def Random_Forest(filename):

	filename = "/Users/Jacob/SparkService/data/sample_libsvm_data.txt"
	# Load and parse the data file into an RDD of LabeledPoint.
	data = MLUtils.loadLibSVMFile(sc, filename)
	# Split the data into training and test sets (30% held out for testing)
	(trainingData, testData) = data.randomSplit([0.7, 0.3])

	# Train a RandomForest model.
	#  Empty categoricalFeaturesInfo indicates all features are continuous.
	#  Note: Use larger numTrees in practice.
	#  Setting featureSubsetStrategy="auto" lets the algorithm choose.
	model = RandomForest.trainClassifier(trainingData, numClasses=2, categoricalFeaturesInfo={},
	                                     numTrees=3, featureSubsetStrategy="auto",
	                                     impurity='gini', maxDepth=4, maxBins=32)

	# Evaluate model on test instances and compute test error
	predictions = model.predict(testData.map(lambda x: x.features))
	labelsAndPredictions = testData.map(lambda lp: lp.label).zip(predictions)
	testErr = labelsAndPredictions.filter(lambda (v, p): v != p).count() / float(testData.count())
	print('Test Error = ' + str(testErr))
	print('Learned classification forest model:')
	print(model.toDebugString())

	# Save and load model
	#model.save(sc, "target/tmp/myRandomForestClassificationModel")
	#sameModel = RandomForestModel.load(sc, "target/tmp/myRandomForestClassificationModel")

def Alternating_Least_Squares(filename):
	# Load and parse the data
	filename = "/Users/Jacob/SparkService/data/ALS_test.data"
	data = sc.textFile(filename)
	ratings = data.map(lambda l: l.split(','))\
	    .map(lambda l: Rating(int(l[0]), int(l[1]), float(l[2])))

	# Build the recommendation model using Alternating Least Squares
	rank = 10
	numIterations = 10
	model = ALS.train(ratings, rank, numIterations)

	# Evaluate the model on training data
	testdata = ratings.map(lambda p: (p[0], p[1]))
	predictions = model.predictAll(testdata).map(lambda r: ((r[0], r[1]), r[2]))
	ratesAndPreds = ratings.map(lambda r: ((r[0], r[1]), r[2])).join(predictions)
	MSE = ratesAndPreds.map(lambda r: (r[1][0] - r[1][1])**2).mean()
	print("Mean Squared Error = " + str(MSE))

	# Save and load model
	#model.save(sc, "target/tmp/myCollaborativeFilter")
	#sameModel = MatrixFactorizationModel.load(sc, "target/tmp/myCollaborativeFilter")

def Isotonic_Regression(filename):
	filename = "/Users/Jacob/SparkService/data/sample_isotonic_regression_data.txt"

	data = sc.textFile(filename)

	# Create label, feature, weight tuples from input data with weight set to default value 1.0.
	parsedData = data.map(lambda line: tuple([float(x) for x in line.split(',')]) + (1.0,))

	# Split data into training (60%) and test (40%) sets.
	training, test = parsedData.randomSplit([0.6, 0.4], 11)

	# Create isotonic regression model from training data.
	# Isotonic parameter defaults to true so it is only shown for demonstration
	model = IsotonicRegression.train(training)

	# Create tuples of predicted and real labels.
	predictionAndLabel = test.map(lambda p: (model.predict(p[1]), p[0]))

	# Calculate mean squared error between predicted and real labels.
	meanSquaredError = predictionAndLabel.map(lambda pl: math.pow((pl[0] - pl[1]), 2)).mean()
	print("Mean Squared Error = " + str(meanSquaredError))

	# Save and load model
	model.save(sc, "target/tmp/myIsotonicRegressionModel")
	sameModel = IsotonicRegressionModel.load(sc, "target/tmp/myIsotonicRegressionModel")

main()	
