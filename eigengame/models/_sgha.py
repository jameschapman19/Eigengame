"""
Gen-Oja: A Simple and Efficient Algorithm for
Streaming Generalized Eigenvector Computation
https://proceedings.neurips.cc/paper/2018/file/1b318124e37af6d74a03501474f44ea1-Paper.pdf
"""
from functools import partial

import jax
import jax.numpy as jnp
import optax
from jax import jit

from ._pcamixin import _PCAMixin
from ._baseexperiment import _BaseExperiment

class SGHA(_PCAMixin, _BaseExperiment):
    def __init__(self, mode, init_rng, config):
        super(SGHA, self).__init__(mode, init_rng, config)
        """Constructs the experiment.
        Args:
          mode: A string, equivalent to FLAGS.jaxline_mode when running normally.
          init_rng: A `PRNGKey` to use for experiment initialization.
        """
        """Initialization function for a Jaxline experiment."""
        self._V = (
                      jax.random.normal(self.local_rng, (config.n_components, self.dims))
                  ) / 1000
        self._update_with_grads = jax.jit(
            jax.vmap(
                self._update_with_grads,
                in_axes=(0, 1, 0),
            )
        )
        self._optimizer = optax.sgd(learning_rate=learning_rate)
        self._opt_state = self._optimizer.init(self._V)

    def _update(self, views, global_step):
        X_i = views
        grad = self._grad(X_i, self._V)
        self._V, self._opt_state = self._update_with_grads(
            self._V, grad, self._opt_state
        )
        norm = jnp.linalg.norm(self._V, axis=1, keepdims=True)
        norm = norm.at[norm < 1].set(1)
        self._V /= norm

    @staticmethod
    @jit
    def _grad(X_i, W):
        n = X_i.shape[0]
        A = X_i.T @ X_i / n
        Y = W @ A @ W.T
        return W.T @ jnp.triu(Y) - A @ W.T

    @partial(jit, static_argnums=(0))
    def _update_with_grads(self, wi, grads, opt_state):
        updates, opt_state = self._optimizer.update(grads, opt_state)
        wi_new = optax.apply_updates(wi, updates)
        return wi_new, opt_state
