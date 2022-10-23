import numpy as np  #allowed
from preorderTreeVisualise import plot_preorder_tree #own file
import pickle #from Python standard library (allowed)
# from convertToPreorder import convert_to_preorder_array #own file


class Node:
#Tree node

    def __init__(self):
        self.true_child = self.false_child = None   #left and right children initially pointing to None.


class Decision (Node):
#for non-leaves. Inherits Node class. Stores attribute and value of decision

    def __init__(self, attribute, value):
        super().__init__() #run inherited __init__() first
        self.attribute = attribute  #which wifi emitter to split by (column index)
        self.value = value  #value by which to split into two subsets, for a given attribute


class Leaf (Node):
#for leaves. Inherits Node class. Stores class label (room no.) for prediction
    
    def __init__(self, room):
        super().__init__() #run inherited __init__() first
        self.room = room   #final predicted class label


class DecisionTree:
#Tree stores root node

    #constructor for a tree
    def __init__(self):
        self.root = None    #beginning of tree
        self.final_depth = None  #used in case final tree depth is < max depth
    
    #save model to text file after training
    def save_tree (self):
        pass

    #rebuild tree from saved model for predicting
    def load_tree (self, filepath):
        pass

    #recursively add nodes to list of lists and preorder list
    @classmethod
    def tree_lists(cls, node, tree_list, preorder_list, max_level, level, num):
        if node is None or level > max_level:   #cease recursion at end of tree or sufficient depth
            diff = max_level - (level-1)    # Need to insert Nones for perfect tree. dictates the number of compeletely None levels we need to insert
            for i in range(diff):       # for each remaining level
                for j in range(2**i): 
                    preorder_list.append(None)  # Place down the appropriate amount of Nones depending on the level we're on right now
            return tree_list, preorder_list     #returns a human-readbale list and a plottable list (respectively) 
        else:
            label_string = f"Emitter {node.attribute} < {node.value}" if type(node) is Decision else f"Room {node.room}"
            tree_list[level-1][num] = label_string      # list of decision labels/rooms for human readability
            preorder_list.append(label_string)
            tree_list, preorder_list = DecisionTree.tree_lists(node.true_child, tree_list, preorder_list, max_level, level+1, 2*num) #level-order node number = 2*num for left branches
            tree_list, preorder_list = DecisionTree.tree_lists(node.false_child, tree_list, preorder_list, max_level, level+1, 2*num + 1) #level-order node number = 2*num + 1 for right branches
        return tree_list, preorder_list
    
    #traverses tree for prediction
    def search_tree(self, node, test_vals):
        if type(node) is Leaf:
            return node.room    #return final room prediction from leaf of tree
        elif test_vals[node.attribute] < node.value:    #check if (test) wifi strength on emitter (from tree) is less than node's decision value 
            return self.search_tree(node.true_child, test_vals) #go down left recursively
        else:
            return self.search_tree(node.true_child, test_vals) #go down right recursively
    
    #creates a nested level-order tree list for human-readability, and an inorder list for plotting
    def print_tree (self, depth=999999):
        list_depth = min(depth, self.final_depth) #print depth can be overwritten by arg
        tree_list = [[None for node in range(2**level)] for level in range(list_depth)] #blank nested list with perfect tree size
        tree_list, preorder_list = DecisionTree.tree_lists(self.root, tree_list, [], list_depth, level=1, num=0)  #traverse tree and add to list
        print("Tree list:\n")
        for row in tree_list:   #human readable, level-order
            print(row)
        print("Preorder list\n")
        print(preorder_list)     #to send for plotting
        plot_preorder_tree(preorder_list, list_depth)
        # converted_preorder_list = convert_to_preorder_array(tree_list)      # converted 2D array into a preorder 1D array for the plot
        # plot_preorder_tree(converted_preorder_list, list_depth)          #separate plot script
        # plot_preorder_tree([1,2,None,4,5,6,None], 3) #separate preorder plot script


class Classifier:
#contains functions and class variables outside the DecisionTree scope

    max_depth = None    #early stopping criteria for trees
    dataset = None  #full data array from file

    @classmethod 
    def entropy_calc(cls, split_array):       # calculation of the entropy for a specific column split (top or bottom)
        unique, counts = np.unique(split_array[:,1], return_counts=True) #frequency of each room in array
        sum = np.sum(counts)    #total number of rooms (equals length of split_array along axis 0)
        proportions = counts / sum    #proportions of each room in the set
        entropies = -1 * proportions * np.log2(proportions) #entropies for each room in the set
        entropy = np.sum(entropies) #total entropy for this split
        return entropy
    
    @classmethod
    def find_split(cls, dataset):   # entropy_for_all_columns
        min_entropy = 999999
        min_router = -1 #default value which should be overwritten
        min_split = -1 #default value which should be overwritten

        numcols = np.size(dataset,1)    #number of columns 
        for emitter in range(numcols-1):      #for each column
            min_col_entropy = 999999    #will be replaced with lowest entropy
            data = dataset[:,[emitter,-1]]    # extract the router column and label
            sorted_data = data[data[:, 0].argsort()]    # sort according to the router column values (makes splits more efficient)         
            print("Emitter:: ", emitter)
            for split_point_index in range(1,len(sorted_data)):     #for each emitter value
                less_split_array = sorted_data[:split_point_index]  # top half of the split column in array form
                greater_split_array = sorted_data[split_point_index:] # bottom half of the split column in array form
                # print("l_split_arr:", less_split_array)
                # print("g_split_arr:", greater_split_array)
                sum_entropy = Classifier.entropy_calc(less_split_array) + Classifier.entropy_calc(greater_split_array) # sum entropies which is used in information gain
                # print("inside:", str(less_split_array))
                # print(sum_entropy < min_col_entropy,"=>", sum_entropy,",", min_col_entropy)
                if sum_entropy < min_col_entropy:   # Checks if the entropy that was just calculated is lower than the lowest for this emitter so far
                    min_col_entropy = sum_entropy       # Minimum entropy for this emitter
                    min_col_split = less_split_array[-1][0]   # Which split value gave the lowest entropy sum for this emitter
            print("min entropy: "+ str(min_entropy) + "; min_split (row value where to split): " + str(min_split)) ######

            # print(min_col_entropy < min_entropy,"=>", min_col_entropy,",", min_entropy)
            if min_col_entropy < min_entropy:   # Checks if the entropy that was just calculated is lower than the lowest so far
                min_entropy = min_col_entropy   # Replaces the value of the return variable with the entropy that was just calculated
                min_split = min_col_split       # Which split value gave the lowest entropy sum overall
                min_router = emitter            # Stores the index of the router with the best split so far

            print("min router: "+ str(min_router) + "; min_split (row value where to split): " +str(min_split)) ######
        # print("outside less split:", str(sorted_data[:min_split]))
        # print("outside sorted data:", str(sorted_data))
        print("outside dataset:", str(dataset[:,-1]))
        assert(min_router!=-1 and min_split!=-1), "Decision tree training error"#+ ("l_split_arr:", str(less_split_array))+ ("g_split_arr:", str(greater_split_array)) #error handling
        #print("g_split_arr:", greater_split_array)
        return min_router, min_split   # Returns the min router(column index) and the split(row index) for this.
        
    #recursive function which constructs tree and returns subtree root node
    @classmethod
    def decision_tree_learning (cls, data, depth):
        room_labels, label_counts = np.unique(data[:, 7], return_counts=True) #get room labels and frequencies present in current subset
        if len(room_labels) == 1 or depth == Classifier.max_depth:    #if all samples from the same room or max_depth reached (early stopping)
            room_plurality = room_labels[label_counts==max(label_counts)][0]   #predicted room is mode of room labels
            leaf_node = Leaf(room_plurality)    #create leaf node with this room prediction
            return leaf_node, depth     #return leaf node and current depth to parent node
        else:
            attribute, value = Classifier.find_split(data)    #find optimal attribute and value to split by for this subset
            decision_node = Decision(attribute, value)        #create new node based on split choices
            print("Attribute:", attribute)
            print("Value:", value)
            true_subset = data[data[:, attribute]<value]      #subset which follows the condition "attribute < value"
            print("true_subset:", true_subset)
            false_subset = data[data[:, attribute]>=value]    #complement set (doesn't follow condition)
            print("false_subset:", false_subset)
            print("-------------------")
            decision_node.true_child, true_subtree_depth = Classifier.decision_tree_learning(true_subset, depth+1) #recursive call on true side of dataset
            decision_node.false_child, false_subtree_depth = Classifier.decision_tree_learning(false_subset, depth+1) #recursive call on false side of dataset
            return (decision_node, max(true_subtree_depth, false_subtree_depth)) #returns node and current max depth to parent node

    #callable by other functions to commence training
    @classmethod
    def fit (cls, dataset, max_depth):
        Classifier.max_depth = max_depth    #tree will stop constructing when this depth is reached
        Classifier.dataset = dataset
        tree = DecisionTree()     #instantiate blank tree
        tree.root, tree.final_depth = Classifier.decision_tree_learning(Classifier.dataset, depth=1)  #start recursive training process
        return tree

    #querying algorithm to traverse through the decision tree to allocate room numbers to test data entered
    @classmethod
    def predict (cls, tree, test_set):
        predictions = []
        test_set = np.array([test_set]) if test_set.ndim == 1 else test_set #ensure that test_set has n tests in it (2D array)
        for test in test_set:   #complete prediction for each test
            predictions.append(tree.search_tree(tree.root, test))
        predictions = np.array(predictions)
        return predictions  #1D array of class labels (rooms) for each test

#default main when file ran individually
if __name__ == "__main__":
    dataset = np.loadtxt(r'intro2ML-coursework1\wifi_db\noisy_dataset.txt').astype(np.int64)    #load data from text file into integer numpy array
    tree = Classifier.fit(dataset, max_depth=10)
    print("Prediction: ", Classifier.predict(tree, np.array([-64, -56, -61, -66, -71, -82, -81])))
    tree.print_tree()

    #-64 -56 -61 -66 -71 -82 -81 1


