<div itemscope itemtype="http://developers.google.com/ReferenceObject">
<meta itemprop="name" content="tfds.core.DatasetBuilder" />
<meta itemprop="path" content="Stable" />
<meta itemprop="property" content="builder_config"/>
<meta itemprop="property" content="info"/>
<meta itemprop="property" content="__init__"/>
<meta itemprop="property" content="as_dataset"/>
<meta itemprop="property" content="download_and_prepare"/>
<meta itemprop="property" content="numpy_iterator"/>
<meta itemprop="property" content="DATA_CONFIGS"/>
<meta itemprop="property" content="builder_configs"/>
<meta itemprop="property" content="name"/>
</div>

# tfds.core.DatasetBuilder

## Class `DatasetBuilder`





Defined in [`core/dataset_builder.py`](https://github.com/tensorflow/datasets/tree/master/tensorflow_datasets/core/dataset_builder.py).

Abstract base class for datasets.

Typical usage:

```python
mnist_builder = tfds.MNIST(data_dir="~/tfds_data")
mnist_builder.download_and_prepare()
train_dataset = mnist_builder.as_dataset(tfds.Split.TRAIN)
assert isinstance(train_dataset, tf.data.Dataset)

# And then the rest of your input pipeline
train_dataset = train_dataset.repeat().shuffle(1024).batch(128)
train_dataset = train_dataset.prefetch(tf.data.experimental.AUTOTUNE)
features = train_dataset.make_one_shot_iterator().get_next()
image, label = features['image'], features['label']
```

<h2 id="__init__"><code>__init__</code></h2>

``` python
__init__(
    data_dir=None,
    config=None
)
```

Construct a DatasetBuilder.

Callers must pass arguments as keyword arguments.

#### Args:

* <b>`data_dir`</b>: (str) directory to read/write data. Defaults to
    "~/tensorflow_datasets".
* <b>`config`</b>: (<a href="../../tfds/core/BuilderConfig.md"><code>tfds.core.BuilderConfig</code></a> or `str` name) optional configuration
    for the dataset that affects the data generated on disk. Different
    `builder_config`s will have their own subdirectories and versions.



## Properties

<h3 id="builder_config"><code>builder_config</code></h3>



<h3 id="info"><code>info</code></h3>

Return the dataset info object. See `DatasetInfo` for details.



## Methods

<h3 id="as_dataset"><code>as_dataset</code></h3>

``` python
as_dataset(
    split,
    shuffle_files=None,
    as_supervised=False
)
```

Constructs a `tf.data.Dataset`.

Callers must pass arguments as keyword arguments.

Subclasses must override _as_dataset.

#### Args:

* <b>`split`</b>: <a href="../../tfds/Split.md"><code>tfds.Split</code></a>, which subset of the data to read.
* <b>`shuffle_files`</b>: `bool` (optional), whether to shuffle the input files.
    Defaults to `True` if `split == tfds.Split.TRAIN` and `False` otherwise.
* <b>`as_supervised`</b>: `bool`, if `True`, the returned `tf.data.Dataset`
    will have a 2-tuple structure `(input, label)` according to
    `builder.info.supervised_keys`. If `False`, the default,
    the returned `tf.data.Dataset` will have a dictionary with all the
    features.


#### Returns:

`tf.data.Dataset`

<h3 id="download_and_prepare"><code>download_and_prepare</code></h3>

``` python
download_and_prepare(
    download_dir=None,
    extract_dir=None,
    manual_dir=None,
    mode=None,
    compute_stats=True
)
```

Downloads and prepares dataset for reading.

Subclasses must override _download_and_prepare.

#### Args:

* <b>`download_dir`</b>: `str`, directory where downloaded files are stored.
    Defaults to "~/tensorflow-datasets/downloads".
* <b>`extract_dir`</b>: `str`, directory where extracted files are stored.
    Defaults to "~/tensorflow-datasets/extracted".
* <b>`manual_dir`</b>: `str`, read-only directory where manually downloaded/extracted
    data is stored. Defaults to
    "~/tensorflow-datasets/manual/{dataset_name}".
* <b>`mode`</b>: <a href="../../tfds/download/GenerateMode.md"><code>tfds.GenerateMode</code></a>: Mode to FORCE_REDOWNLOAD,
    or REUSE_DATASET_IF_EXISTS. Defaults to REUSE_DATASET_IF_EXISTS.
* <b>`compute_stats`</b>: `boolean` If True, compute statistics over the generated
    data and write the <a href="../../tfds/core/DatasetInfo.md"><code>tfds.core.DatasetInfo</code></a> protobuf to disk.


#### Raises:

* <b>`ValueError`</b>: If the user defines both cache_dir and dl_manager

<h3 id="numpy_iterator"><code>numpy_iterator</code></h3>

``` python
numpy_iterator(**as_dataset_kwargs)
```

Generates numpy elements from the given <a href="../../tfds/Split.md"><code>tfds.Split</code></a>.

This generator can be useful for non-TensorFlow programs.

#### Args:

* <b>`**as_dataset_kwargs`</b>: Keyword arguments passed on to
    <a href="../../tfds/core/DatasetBuilder.md#as_dataset"><code>tfds.core.DatasetBuilder.as_dataset</code></a>.


#### Returns:

Generator yielding feature dictionaries
`dict<str feature_name, numpy.array feature_val>`.



## Class Members

<h3 id="DATA_CONFIGS"><code>DATA_CONFIGS</code></h3>

<h3 id="builder_configs"><code>builder_configs</code></h3>

<h3 id="name"><code>name</code></h3>

