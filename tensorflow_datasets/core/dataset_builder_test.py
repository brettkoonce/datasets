# coding=utf-8
# Copyright 2018 The TensorFlow Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for tensorflow_datasets.core.dataset_builder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import tensorflow as tf
from tensorflow_datasets.core import dataset_builder
from tensorflow_datasets.core import dataset_info
from tensorflow_datasets.core import features
from tensorflow_datasets.core import registered
from tensorflow_datasets.core import splits
from tensorflow_datasets.core import test_utils

tf.enable_eager_execution()


class DummyDatasetSharedGenerator(dataset_builder.GeneratorBasedBuilder):

  def _split_generators(self, dl_manager):
    # Split the 30 examples from the generator into 2 train shards and 1 test
    # shard.
    del dl_manager
    return [splits.SplitGenerator(
        name=[splits.Split.TRAIN, splits.Split.TEST],
        num_shards=[2, 1],
    )]

  def _info(self):
    return dataset_info.DatasetInfo(
        features=features.FeaturesDict({"x": tf.int64}),
        supervised_keys=("x", "x"),
    )

  def _generate_examples(self):
    for i in range(30):
      yield self.info.features.encode_example({"x": i})


class DummyBuilderConfig(dataset_builder.BuilderConfig):

  def __init__(self, increment=0, **kwargs):
    super(DummyBuilderConfig, self).__init__(**kwargs)
    self.increment = increment


class DummyDatasetWithConfigs(dataset_builder.GeneratorBasedBuilder):
  DATA_CONFIGS = [
      DummyBuilderConfig(
          name="plus1",
          version="0.0.1",
          description="Add 1 to the records",
          increment=1),
      DummyBuilderConfig(
          name="plus2",
          version="0.0.2",
          description="Add 2 to the records",
          increment=2),
  ]

  def _split_generators(self, dl_manager):
    # Split the 30 examples from the generator into 2 train shards and 1 test
    # shard.
    del dl_manager
    return [
        splits.SplitGenerator(
            name=[splits.Split.TRAIN, splits.Split.TEST],
            num_shards=[2, 1],
        )
    ]

  def _info(self):
    if self._builder_config:
      version = self._builder_config.version
    else:
      version = "1.0.0"
    return dataset_info.DatasetInfo(
        features=features.FeaturesDict({"x": tf.int64}),
        supervised_keys=("x", "x"),
        version=version,
    )

  def _generate_examples(self):
    for i in range(30):
      if self.builder_config:
        i += self.builder_config.increment
      yield self.info.features.encode_example({"x": i})


class DatasetBuilderTest(tf.test.TestCase):

  def test_shared_generator(self):
    with test_utils.tmp_dir(self.get_temp_dir()) as tmp_dir:
      builder = DummyDatasetSharedGenerator(data_dir=tmp_dir)
      builder.download_and_prepare()

      written_filepaths = [
          os.path.join(builder._data_dir, fname)
          for fname in tf.gfile.ListDirectory(builder._data_dir)
      ]
      # The data_dir contains the cached directory by default
      expected_filepaths = builder._build_split_filenames(
          split_info_list=builder.info.splits.values())
      expected_filepaths.append(
          os.path.join(builder._data_dir, "dataset_info.json"))
      self.assertEqual(sorted(expected_filepaths), sorted(written_filepaths))

      splits_list = [
          splits.Split.TRAIN, splits.Split.TEST
      ]
      datasets = [builder.as_dataset(split=split) for split in splits_list]
      data = [[el["x"].numpy() for el in dataset] for dataset in datasets]

      train_data, test_data = data
      self.assertEqual(20, len(train_data))
      self.assertEqual(10, len(test_data))
      self.assertEqual(list(range(30)), sorted(train_data + test_data))

      # Builder's info should also have the above information.
      self.assertTrue(builder.info.initialized)
      self.assertEqual(20, builder.info.splits[splits.Split.TRAIN].num_examples)
      self.assertEqual(10, builder.info.splits[splits.Split.TEST].num_examples)
      self.assertEqual(30, builder.info.num_examples)

  def test_load(self):
    with test_utils.tmp_dir(self.get_temp_dir()) as tmp_dir:
      dataset = registered.load(
          name="dummy_dataset_shared_generator",
          data_dir=tmp_dir,
          download=True,
          split=splits.Split.TRAIN)
      data = list(dataset)
      self.assertEqual(20, len(data))
      self.assertLess(data[0]["x"], 30)

  def test_get_data_dir(self):
    # Test that the dataset load the most recent dir
    with test_utils.tmp_dir(self.get_temp_dir()) as tmp_dir:
      builder = DummyDatasetSharedGenerator(data_dir=tmp_dir)
      builder_data_dir = os.path.join(tmp_dir, builder.name)

      # The dataset folder contains multiple versions
      tf.gfile.MakeDirs(os.path.join(builder_data_dir, "14.0.0.invalid"))
      tf.gfile.MakeDirs(os.path.join(builder_data_dir, "10.0.0"))
      tf.gfile.MakeDirs(os.path.join(builder_data_dir, "9.0.0"))

      # The last valid version is chosen by default
      most_recent_dir = os.path.join(builder_data_dir, "10.0.0")
      v9_dir = os.path.join(builder_data_dir, "9.0.0")
      self.assertEqual(builder._get_data_dir(), most_recent_dir)
      self.assertEqual(builder._get_data_dir(version="9.0.0"), v9_dir)

  def test_get_data_dir_with_config(self):
    with test_utils.tmp_dir(self.get_temp_dir()) as tmp_dir:
      config_name = "plus1"
      builder = DummyDatasetWithConfigs(config=config_name, data_dir=tmp_dir)

      builder_data_dir = os.path.join(tmp_dir, builder.name, config_name)
      version_data_dir = os.path.join(builder_data_dir, "0.0.1")

      tf.gfile.MakeDirs(version_data_dir)
      self.assertEqual(builder._get_data_dir(), version_data_dir)

  def test_config_construction(self):
    self.assertSetEqual(
        set(["plus1", "plus2"]),
        set(DummyDatasetWithConfigs.builder_configs.keys()))
    plus1_config = DummyDatasetWithConfigs.builder_configs["plus1"]
    builder = DummyDatasetWithConfigs(config="plus1", data_dir=None)
    self.assertIs(plus1_config, builder.builder_config)
    builder = DummyDatasetWithConfigs(config=plus1_config, data_dir=None)
    self.assertIs(plus1_config, builder.builder_config)
    self.assertIs(builder.builder_config,
                  DummyDatasetWithConfigs.DATA_CONFIGS[0])

  def test_with_configs(self):
    with test_utils.tmp_dir(self.get_temp_dir()) as tmp_dir:
      builder1 = DummyDatasetWithConfigs(config="plus1", data_dir=tmp_dir)
      builder2 = DummyDatasetWithConfigs(config="plus2", data_dir=tmp_dir)
      # Test that builder.builder_config is the correct config
      self.assertIs(builder1.builder_config,
                    DummyDatasetWithConfigs.builder_configs["plus1"])
      self.assertIs(builder2.builder_config,
                    DummyDatasetWithConfigs.builder_configs["plus2"])
      builder1.download_and_prepare()
      builder2.download_and_prepare()
      data_dir1 = os.path.join(tmp_dir, builder1.name, "plus1", "0.0.1")
      data_dir2 = os.path.join(tmp_dir, builder2.name, "plus2", "0.0.2")
      # Test that subdirectories were created per config
      self.assertTrue(tf.gfile.Exists(data_dir1))
      self.assertTrue(tf.gfile.Exists(data_dir2))
      # 2 train shards, 1 test shard, plus metadata files
      self.assertGreater(len(tf.gfile.ListDirectory(data_dir1)), 3)
      self.assertGreater(len(tf.gfile.ListDirectory(data_dir2)), 3)

      # Test that the config was used and they didn't collide.
      splits_list = [splits.Split.TRAIN, splits.Split.TEST]
      for builder, incr in [(builder1, 1), (builder2, 2)]:
        datasets = [builder.as_dataset(split=split) for split in splits_list]
        data = [[el["x"].numpy() for el in dataset] for dataset in datasets]

        train_data, test_data = data
        self.assertEqual(20, len(train_data))
        self.assertEqual(10, len(test_data))
        self.assertEqual([incr + el for el in range(30)],
                         sorted(train_data + test_data))


class DatasetBuilderReadTest(tf.test.TestCase):

  @classmethod
  def setUpClass(cls):
    cls._tfds_tmp_dir = test_utils.make_tmp_dir()
    builder = DummyDatasetSharedGenerator(data_dir=cls._tfds_tmp_dir)
    builder.download_and_prepare()

  @classmethod
  def tearDownClass(cls):
    test_utils.rm_tmp_dir(cls._tfds_tmp_dir)

  def test_numpy_iterator(self):
    builder = DummyDatasetSharedGenerator(data_dir=self._tfds_tmp_dir)
    items = []
    for item in builder.numpy_iterator(split=splits.Split.TRAIN):
      items.append(item)
    self.assertEqual(20, len(items))
    self.assertLess(items[0]["x"], 30)

  def test_supervised_keys(self):
    builder = DummyDatasetSharedGenerator(data_dir=self._tfds_tmp_dir)
    for item in builder.numpy_iterator(
        split=splits.Split.TRAIN, as_supervised=True):
      self.assertIsInstance(item, tuple)
      self.assertEqual(len(item), 2)
      break


if __name__ == "__main__":
  tf.test.main()
