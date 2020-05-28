"""A popular speech model.

Authors: Mirco Ravanelli 2020, Peter Plantinga 2020, Ju-Chieh Chou 2020,
    Titouan Parcollet 2020, Abdel 2020
"""
import torch
from speechbrain.nnet.RNN import RNN
from speechbrain.nnet.CNN import Conv
from speechbrain.nnet.linear import Linear
from speechbrain.nnet.pooling import Pooling
from speechbrain.nnet.dropout import Dropout
from speechbrain.nnet.containers import Sequential
from speechbrain.nnet.normalization import Normalize


class CRDNN(Sequential):
    """This model is a combination of CNNs, RNNs, and DNNs.

    The default CNN model is based on VGG.

    Arguments
    ---------
    activation : torch class
        A class used for constructing the activation layers. For cnn and dnn.
    dropout : float
        Neuron dropout rate, applied to cnn, rnn, and dnn.
    cnn_blocks : int
        The number of convolutional neural blocks to include.
    cnn_channels : list of ints
        A list of the number of output channels for each cnn block.
    cnn_kernelsize : tuple of ints
        The size of the convolutional kernels.
    time_pooling : bool
        Whether to pool the utterance on the time axis before the RNN.
    time_pooling_size : int
        The number of elements to pool on the time axis.
    time_pooling_stride : int
        The number of elements to increment by when iterating the time axis.
    rnn_layers : int
        The number of recurrent neural layers to include.
    rnn_type : string
        See `speechbrain.nnet.RNN.RNN` for a list of options.
    rnn_neurons : int
        Number of neurons in each layer of the RNN.
    rnn_bidirectional : bool
        Whether this model will process just forward or both directions.
    dnn_blocks : int
        The number of linear neural blocks to include.
    dnn_neurons : int
        The number of neurons in the linear layers.

    Example
    -------
    >>> model = CRDNN()
    >>> inputs = torch.rand([10, 120, 60])
    >>> outputs = model(inputs, init_params=True)
    >>> outputs.shape
    torch.Size([10, 120, 512])
    """

    def __init__(
        self,
        activation=torch.nn.LeakyReLU,
        dropout=0.15,
        cnn_blocks=2,
        cnn_channels=[128, 256],
        cnn_kernelsize=(3, 3),
        time_pooling=False,
        time_pooling_size=2,
        time_pooling_stride=2,
        rnn_layers=4,
        rnn_type="lstm",
        rnn_neurons=512,
        rnn_bidirectional=True,
        dnn_blocks=2,
        dnn_neurons=512,
    ):
        blocks = []

        for block_index in range(cnn_blocks):
            blocks.extend(
                [
                    Conv(
                        out_channels=cnn_channels[block_index],
                        kernel_size=cnn_kernelsize,
                    ),
                    Normalize(norm_type="batchnorm"),
                    activation(),
                    Conv(
                        out_channels=cnn_channels[block_index],
                        kernel_size=cnn_kernelsize,
                    ),
                    Normalize(norm_type="batchnorm"),
                    activation(),
                    Pooling(pool_type="max", kernel_size=2, stride=2),
                    Dropout(drop_rate=dropout),
                ]
            )

        if time_pooling:
            blocks.append(
                Pooling(
                    pool_type="max",
                    stride=time_pooling_stride,
                    kernel_size=time_pooling_size,
                    pool_axis=1,
                )
            )

        if rnn_layers > 0:
            blocks.append(
                RNN(
                    rnn_type=rnn_type,
                    n_neurons=rnn_neurons,
                    num_layers=rnn_layers,
                    dropout=dropout,
                    bidirectional=rnn_bidirectional,
                )
            )

        for block_index in range(dnn_blocks):
            blocks.extend(
                [
                    Linear(
                        n_neurons=dnn_neurons, bias=True, combine_dims=False,
                    ),
                    Normalize(norm_type="batchnorm"),
                    activation(),
                    Dropout(drop_rate=dropout),
                ]
            )

        super().__init__(*blocks)