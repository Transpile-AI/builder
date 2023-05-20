# global
import os
import ivy
import pytest

# local
import ivy_builder.builder as builder
import ivy_builder_tests.helpers as builder_helpers

# Simple Example #

from ivy_builder_demos import full_example, simple_example
from ivy_builder_demos.simple_example import ExampleDataLoader as ExampleDataLoaderMin
from ivy_builder_demos.simple_example import ExampleNetwork as ExampleNetworkMin
from ivy_builder_demos.simple_example import ExampleTrainer as ExampleTrainerMin

# Full Example #

from ivy_builder_demos.full_example import (
    ExampleDatasetDirs,
    ExampleDatasetSpec,
    ExampleDataLoaderSpec,
    ExampleDataLoader,
    ExampleNetworkSpec,
    ExampleNetwork,
    ExampleTrainer,
)


# Tests #
# ------#


@pytest.mark.parametrize("compile_mode", ["all", False])
def test_simple_trainers(dev_str, compile_mode, fw):
    compile_mode = compile_mode
    # test
    builder_helpers.remove_dirs()
    simple_example.main(compile_mode=compile_mode)
    builder_helpers.remove_dirs()


@pytest.mark.parametrize("compile_mode", ["all", False])
def test_simple_multi_dev_trainers(dev_str, compile_mode, fw):

    compile_mode = compile_mode

    # devices
    dev_strs = list()
    dev_str0 = dev_str
    dev_strs.append(dev_str0)
    if "gpu" in dev_str:
        idx = ivy.num_gpus() - 1
        dev_str1 = dev_str[:-1] + str(idx)
        dev_strs.append(dev_str1)

    # test
    builder_helpers.remove_dirs()
    simple_example.main(compile_mode=compile_mode, dev_strs=dev_strs)
    builder_helpers.remove_dirs()


@pytest.mark.parametrize("compile_mode", ["all", False])
def test_full_trainers(dev_str, compile_mode, fw):
    compile_mode = compile_mode
    # test
    builder_helpers.remove_dirs()
    full_example.main(compile_mode=compile_mode)
    builder_helpers.remove_dirs()


@pytest.mark.parametrize("compile_mode", ["all", False])
def test_visualizing(dev_str, compile_mode, fw):

    compile_mode = compile_mode
    builder_helpers.remove_dirs()
    data_loader_spec_args = {"batch_size": 1, "dev_strs": [dev_str]}
    trainer_spec_args = {
        "total_iterations": 10,
        "ld_chkpt": False,
        "save_freq": 1,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoaderMin,
        ExampleNetworkMin,
        ExampleTrainerMin,
        data_loader_spec_args=data_loader_spec_args,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    try:
        trainer.visualize()
    except OSError:
        pass
    trainer.close()
    builder_helpers.remove_dirs()


@pytest.mark.parametrize("compile_mode", ["all", False])
def test_checkpoint_loading(dev_str, compile_mode, fw):
    compile_mode = compile_mode

    builder_helpers.remove_dirs()
    data_loader_spec_args = {"batch_size": 1, "dev_strs": [dev_str]}
    trainer_spec_args = {
        "total_iterations": 10,
        "ld_chkpt": False,
        "save_freq": 1,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoaderMin,
        ExampleNetworkMin,
        ExampleTrainerMin,
        data_loader_spec_args=data_loader_spec_args,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    trainer.train()
    trainer.close()
    trainer_spec_args = {
        "total_iterations": 20,
        "ld_chkpt": True,
        "save_freq": 1,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoaderMin,
        ExampleNetworkMin,
        ExampleTrainerMin,
        data_loader_spec_args=data_loader_spec_args,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    trainer.train()
    trainer.close()
    checkpoint_nums = [
        int(fname.split("-")[-1].split(".")[0]) for fname in os.listdir("log/chkpts")
    ]
    assert max(checkpoint_nums) == 19
    builder_helpers.remove_dirs()


@pytest.mark.parametrize("compile_mode", ["all", False])
def test_reduced_cost_after_checkpoint_load(dev_str, compile_mode, fw):

    example_dir = os.path.relpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../ivy_builder_demos")
    )


    compile_mode = compile_mode

    # dataset dirs specification
    dataset_dirs_args = dict()

    # dataset specification
    dataset_spec_filepath = os.path.join(
        example_dir, "json_specs", "dataset_spec.json.example"
    )
    dataset_spec_args = builder.parse_json_to_cont(dataset_spec_filepath)

    # data loader specification
    data_loader_spec_filepath = os.path.join(
        example_dir, "json_specs", "data_loader_spec.json.example"
    )
    data_loader_spec_args = builder.parse_json_to_cont(data_loader_spec_filepath)

    # network specification
    network_spec_filepath = os.path.join(
        example_dir, "json_specs", "network_spec.json.example"
    )
    network_spec_args = builder.parse_json_to_cont(network_spec_filepath)

    builder_helpers.remove_dirs()

    ivy.seed(seed_value=0)
    trainer_spec_args = {
        "total_iterations": 1,
        "ld_chkpt": False,
        "save_freq": 1,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoader,
        ExampleNetwork,
        ExampleTrainer,
        dataset_dirs_args=dataset_dirs_args,
        dataset_dirs_class=ExampleDatasetDirs,
        dataset_spec_args=dataset_spec_args,
        dataset_spec_class=ExampleDatasetSpec,
        data_loader_spec_args=data_loader_spec_args,
        data_loader_spec_class=ExampleDataLoaderSpec,
        network_spec_args=network_spec_args,
        network_spec_class=ExampleNetworkSpec,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    trainer.train()
    initial_cost = trainer._total_cost
    assert trainer._global_step == 1
    trainer.close()

    ivy.seed(seed_value=0)
    steps_to_take_first = 10
    trainer_spec_args = {
        "total_iterations": steps_to_take_first,
        "ld_chkpt": False,
        "save_freq": 1,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoader,
        ExampleNetwork,
        ExampleTrainer,
        dataset_dirs_args=dataset_dirs_args,
        dataset_dirs_class=ExampleDatasetDirs,
        dataset_spec_args=dataset_spec_args,
        dataset_spec_class=ExampleDatasetSpec,
        data_loader_spec_args=data_loader_spec_args,
        data_loader_spec_class=ExampleDataLoaderSpec,
        network_spec_args=network_spec_args,
        network_spec_class=ExampleNetworkSpec,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    trainer.train()
    ten_step_cost = trainer._total_cost
    assert trainer._global_step == steps_to_take_first
    trainer.close()
    assert initial_cost > ten_step_cost

    steps_to_take_second = 20
    trainer_spec_args = {
        "total_iterations": steps_to_take_second,
        "ld_chkpt": True,
        "save_freq": 1,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoader,
        ExampleNetwork,
        ExampleTrainer,
        dataset_dirs_args=dataset_dirs_args,
        dataset_dirs_class=ExampleDatasetDirs,
        dataset_spec_args=dataset_spec_args,
        dataset_spec_class=ExampleDatasetSpec,
        data_loader_spec_args=data_loader_spec_args,
        data_loader_spec_class=ExampleDataLoaderSpec,
        network_spec_args=network_spec_args,
        network_spec_class=ExampleNetworkSpec,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    trainer.train()
    twenty_step_cost = trainer._total_cost
    assert trainer._global_step == steps_to_take_second
    trainer.close()
    assert ten_step_cost > twenty_step_cost
    builder_helpers.remove_dirs()


@pytest.mark.parametrize("compile_mode", ["all", False])
def test_checkpoint_save_and_restore_via_public_trainer_methods(
    dev_str, compile_mode, fw
):

    compile_mode = compile_mode

    builder_helpers.remove_dirs()
    data_loader_spec_args = {"batch_size": 1, "dev_strs": [dev_str]}
    trainer_spec_args = {
        "total_iterations": 0,
        "ld_chkpt": False,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoaderMin,
        ExampleNetworkMin,
        ExampleTrainerMin,
        data_loader_spec_args=data_loader_spec_args,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    chkpt0_path = os.path.join("chkpt/", "test_chkpt0.hdf5")
    trainer.save(chkpt0_path)
    assert os.path.exists(chkpt0_path)
    trainer.train()
    chkpt1_path = os.path.join("chkpt/", "test_chkpt1.hdf5")
    trainer.save(chkpt1_path)
    trainer.close()
    assert os.path.exists(chkpt1_path)

    data_loader_spec_args = {"batch_size": 1, "dev_strs": [dev_str]}
    trainer_spec_args = {
        "total_iterations": 10,
        "ld_chkpt": False,
        "save_freq": 1,
        "compile_mode": compile_mode,
    }
    trainer = builder.build_trainer(
        ExampleDataLoaderMin,
        ExampleNetworkMin,
        ExampleTrainerMin,
        data_loader_spec_args=data_loader_spec_args,
        trainer_spec_args=trainer_spec_args,
    )
    trainer.setup()
    trainer.restore(chkpt0_path)
    trainer.train()
    chkpt3_path = os.path.join("chkpt/", "test_chkpt3.hdf5")
    trainer.save(chkpt3_path)
    trainer.close()
    assert os.path.exists(chkpt3_path)
    builder_helpers.remove_dirs()
