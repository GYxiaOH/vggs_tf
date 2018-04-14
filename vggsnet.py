"""This is an TensorFLow implementation of vggs.

you can see the detail about vggs in 
https://gist.github.com/ksimonyan/fd8800eeb36e276cd6f9#file-readme-md

Author: GYxiaOH
contact: zhhy1994226@163.com
"""

import tensorflow as tf
import numpy as np


class VggsNet(object):
    """Implementation of the VggsNet."""

    def __init__(self, x, keep_prob, num_classes, skip_layer,
                 weights_path='DEFAULT'):
        """Create the graph of the AlexNet model.

        Args:
            x: Placeholder for the input tensor.
            keep_prob: Dropout probability.
            num_classes: Number of classes in the dataset.
            skip_layer: List of names of the layer, that get trained from
                scratch,i change it to make weights can be trained
            weights_path: Complete path to the pretrained weight file, if it
                isn't in the same folder as this code
        """
        # Parse input arguments into class variables
        self.X = x
        self.NUM_CLASSES = num_classes
        self.KEEP_PROB = keep_prob
        self.SKIP_LAYER = skip_layer

        if weights_path == 'DEFAULT':
            self.WEIGHTS_PATH = 'prevgg.npy'
        else:
            self.WEIGHTS_PATH = weights_path

        # Call the create function to build the computational graph of AlexNet
        self.create()

    def create(self):
        # """Create the network graph."""

        conv1 = conv(self.X,7, 7, 96, 2, 2, padding='VALID', name='conv1')
        norm1 = lrn(conv1,2, 0.00010000000475, 0.75, name='norm1')
        pool1 = max_pool(norm1,3, 3, 3, 3, name='pool1')


        conv2 = conv(pool1,5, 5, 256, 1, 1, padding='VALID', name='conv2')
        pool2 = max_pool(conv2,2, 2, 2, 2, name='pool2')

        conv3 = conv(pool2,3, 3, 512, 1, 1, name='conv3')
        conv4 = conv(conv3,3, 3, 512, 1, 1, name='conv4')

        conv5 = conv(conv4,3, 3, 512, 1, 1, name='conv5')
        pool5 = max_pool(conv5,3, 3, 3, 3, name='pool5')

        flattended = tf.reshape(pool5,[-1,6*6*512])
        fc6 = fc(flattended,6*6*512,4096, name='fc6')
        dropout6 = dropout(fc6, self.KEEP_PROB)

        fc7 = fc(dropout6,4096,4096, name='fc7')
        dropout7 = dropout(fc7, self.KEEP_PROB)

        self.fc7 = fc7
        self.fc8 = tf.layers.dense(dropout7,self.NUM_CLASSES,name='fc8')


    def load_initial_weights(self, session):
        """Load weights from file into network.

        As the weights from http://www.cs.toronto.edu/~guerzhoy/tf_alexnet/
        Maybe the weights geted from caffe to tensorflow are different to above
	weights,it's a dict of dict
        """
        # Load the weights into memory
        weights_dict = np.load(self.WEIGHTS_PATH, encoding='bytes').item()

        # Loop over all layer names stored in the weights dict
        for op_name in weights_dict:

            # Check if layer should be trained from scratch
            if op_name not in self.SKIP_LAYER:

                with tf.variable_scope(op_name, reuse=True):


                    # Assign weights/biases to their corresponding tf variable
                    for data in weights_dict[op_name]:

                        # Biases
                        if data == 'biases':
                            var = tf.get_variable('biases', trainable=True)
                            session.run(var.assign(weights_dict[op_name][data]))

                        # Weights
                        else:
                            var = tf.get_variable('weights', trainable=True)
                            session.run(var.assign(weights_dict[op_name][data]))


def conv(x, filter_height, filter_width, num_filters, stride_y, stride_x, name,
         padding='SAME', groups=1):
    """Create a convolution layer.

    Adapted from: https://github.com/ethereon/caffe-tensorflow
    """
    # Get number of input channels
    input_channels = int(x.get_shape()[-1])

    # Create lambda function for the convolution
    convolve = lambda i, k: tf.nn.conv2d(i, k,
                                         strides=[1, stride_y, stride_x, 1],
                                         padding=padding)

    with tf.variable_scope(name) as scope:
        # Create tf variables for the weights and biases of the conv layer
        weights = tf.get_variable('weights', shape=[filter_height,
                                                    filter_width,
                                                    input_channels/groups,
                                                    num_filters])
        biases = tf.get_variable('biases', shape=[num_filters])

    if groups == 1:
        conv = convolve(x, weights)

    # In the cases of multiple groups, split inputs & weights and
    else:
        # Split input and weights and convolve them separately
        input_groups = tf.split(axis=3, num_or_size_splits=groups, value=x)
        weight_groups = tf.split(axis=3, num_or_size_splits=groups,
                                 value=weights)
        output_groups = [convolve(i, k) for i, k in zip(input_groups, weight_groups)]

        # Concat the convolved output together again
        conv = tf.concat(axis=3, values=output_groups)

    # Add biases
    bias = tf.reshape(tf.nn.bias_add(conv, biases), tf.shape(conv))

    # Apply relu function
    relu = tf.nn.relu(bias, name=scope.name)

    return relu


def fc(x, num_in, num_out, name, relu=True):
    """Create a fully connected layer."""
    with tf.variable_scope(name) as scope:

        # Create tf variables for the weights and biases
        weights = tf.get_variable('weights', shape=[num_in, num_out],
                                  trainable=True)
        biases = tf.get_variable('biases', [num_out], trainable=True)

        # Matrix multiply weights and inputs and add bias
        act = tf.nn.xw_plus_b(x, weights, biases, name=scope.name)

    if relu:
        # Apply ReLu non linearity
        relu = tf.nn.relu(act)
        return relu
    else:
        return act


def max_pool(x, filter_height, filter_width, stride_y, stride_x, name,
             padding='SAME'):
    """Create a max pooling layer."""
    return tf.nn.max_pool(x, ksize=[1, filter_height, filter_width, 1],
                          strides=[1, stride_y, stride_x, 1],
                          padding=padding, name=name)


def lrn(x, radius, alpha, beta, name, bias=1.0):
    """Create a local response normalization layer."""
    return tf.nn.local_response_normalization(x, depth_radius=radius,
                                              alpha=alpha, beta=beta,
                                              bias=bias, name=name)


def dropout(x, keep_prob):
    """Create a dropout layer."""
    return tf.nn.dropout(x, keep_prob)
