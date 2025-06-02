# strategy/dp_wrapper.py
import os
import torch
from hydra import initialize, compose
from omegaconf import OmegaConf
from pathlib import Path

from diffusion_policy.workspace.train_diffusion_unet_lowdim_workspace import TrainDiffusionUnetLowdimWorkspace


class DiffusionPolicyWrapper:
    def __init__(self, ckpt_path: str):
        config_path = "../dp_repo/diffusion_policy/config"  
        config_name = "train_diffusion_unet_lowdim_workspace.yaml"

        overrides = [
            "task=pusht_lowdim",
            f'+checkpoint.resume_path="{ckpt_path}"',
            "training.resume=True"
        ]

        print("[DEBUG] __file__ dir:", os.path.dirname(__file__))
        print("[DEBUG] Using config_path:", config_path)
        print("[DEBUG] Overrides:", overrides)

        with initialize(version_base=None, config_path=config_path):
            cfg = compose(config_name=config_name, overrides=overrides)

        self.cfg = cfg
        print("[INFO] Config loaded:")
        print(OmegaConf.to_yaml(cfg))

        self.workspace = TrainDiffusionUnetLowdimWorkspace(cfg)

        ckpt_path = Path(ckpt_path)
        if not ckpt_path.is_absolute():
            ckpt_path = Path(__file__).parent / ckpt_path
        ckpt_path = ckpt_path.expanduser().resolve()

        self.workspace.load_checkpoint(ckpt_path)

        self.policy = self.workspace.model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy.to(self.device)
        self.policy.eval()

    def predict(self, obs_dict):
        """
        obs_dict: dict with key 'obs', shape (T, obs_dim) or (T * obs_dim,)
        """
        obs_array = obs_dict['obs']
        if obs_array.ndim == 1:
            # 从 flat 向量恢复为 (T, obs_dim)
            T = self.cfg.n_obs_steps
            Do = self.cfg.obs_dim
            obs_array = obs_array.reshape((T, Do))

        obs_tensor = torch.tensor(obs_array, dtype=torch.float32).unsqueeze(0).to(self.device)  # (1, T, Do)

        with torch.no_grad():
            action_pred = self.policy.predict_action({'obs': obs_tensor})
            
        print(f"[DP] Input obs shape: {obs_tensor.shape}, Predicted action: {action_pred['action'].cpu().numpy()[0]}")
        assert isinstance(action_pred, dict) and 'action' in action_pred
        return action_pred['action'].cpu().numpy()[0]  # shape (action_dim,)






