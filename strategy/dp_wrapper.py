# strategy/dp_wrapper.py
import os
import torch
from hydra import initialize, compose
from omegaconf import OmegaConf
from pathlib import Path
import numpy as np

from diffusion_policy.workspace.train_diffusion_unet_lowdim_workspace import TrainDiffusionUnetLowdimWorkspace


class DiffusionPolicyWrapper:
    def __init__(self, ckpt_path: str):
        # === Load Config ===
        config_path = "../dp_repo/diffusion_policy/config"
        config_name = "train_diffusion_unet_lowdim_workspace.yaml"

        overrides = [
            "task=pusht_lowdim",
            f'+checkpoint.resume_path="{ckpt_path}"',
            "training.resume=True"
        ]

        print("[INFO] Initializing Diffusion Policy Wrapper...")
        print(f"[INFO] Using config path: {config_path}")
        print(f"[INFO] Loading checkpoint from: {ckpt_path}")

        with initialize(version_base=None, config_path=config_path):
            cfg = compose(config_name=config_name, overrides=overrides)

        self.cfg = cfg
        print("[INFO] Configuration loaded successfully:")
        print(OmegaConf.to_yaml(cfg))

        # === Initialize Workspace ===
        self.workspace = TrainDiffusionUnetLowdimWorkspace(cfg)

        ckpt_path = Path(ckpt_path)
        if not ckpt_path.is_absolute():
            ckpt_path = Path(__file__).parent / ckpt_path
        ckpt_path = ckpt_path.expanduser().resolve()

        self.workspace.load_checkpoint(ckpt_path)

        # === Prepare Model ===
        self.policy = self.workspace.model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy.to(self.device)
        self.policy.eval()

    def predict(self, obs_dict):
        """
        Predict action using the diffusion policy model.
        Args:
            obs_dict: {'obs': np.ndarray} with shape (T, obs_dim) or flat (T * obs_dim,)
        Returns:
            action: np.ndarray of shape (action_dim,)
        """
        obs_array = obs_dict['obs']
        if obs_array.ndim == 1:
            # Convert flat vector to (T, obs_dim)
            T = self.cfg.n_obs_steps
            Do = self.cfg.obs_dim
            obs_array = obs_array.reshape((T, Do))

        obs_tensor = torch.tensor(obs_array, dtype=torch.float32).unsqueeze(0).to(self.device)  # (1, T, Do)

        with torch.no_grad():
            action_pred = self.policy.predict_action({'obs': obs_tensor})

        assert isinstance(action_pred, dict) and 'action' in action_pred
        action_np = action_pred['action'].cpu().numpy()[0]  # shape: (action_dim,)

        print(f"[DP] Action predicted from input of shape {obs_tensor.shape}: {action_np}")
        return action_np


if __name__ == "__main__":
    ckpt = "/home/yinqian/projects/multi_agent_mpd/dp_repo/data/outputs/2025.06.04/20.16.23_train_diffusion_unet_lowdim_pybullet_mcp_lowdim/checkpoints/epoch=0150-test_mean_score=0.098.ckpt"
    dp = DiffusionPolicyWrapper(ckpt)

    # Construct dummy input
    dummy_obs = np.random.rand(2, dp.cfg.obs_dim).astype(np.float32)
    dp.predict({'obs': dummy_obs})
