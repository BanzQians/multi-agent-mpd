# strategy/test_dp_wrapper.py

from strategy.dp_wrapper import DiffusionPolicyWrapper
import numpy as np
import os

ckpt_path = os.path.abspath("dp_repo/data/outputs/2025.05.27/16.21.55_train_diffusion_unet_lowdim_pusht_lowdim/checkpoints/epoch=1300-test_mean_score=0.912.ckpt")

dp_policy = DiffusionPolicyWrapper(ckpt_path)

# obs_dim=20, n_obs_steps=2 → 2行20列
dummy_obs = np.random.randn(2, 20).astype(np.float32)
action = dp_policy.predict({'obs': dummy_obs})
print("Predicted action:", action)

