"""Module for the customization of trimesh's CollisionManager class."""

import fcl
import numpy as np
from trimesh.collision import CollisionManager


class CustomCollisionManager(CollisionManager):
    """Customization of trimesh's CollisionManager class."""

    def transform_object(self, object_name: str,
                         transform_matrix: np.ndarray | list | tuple) -> None:
        transform_matrix = np.asarray(transform_matrix)
        if transform_matrix.shape != (4, 4):
            raise ValueError("Expected transform matrix to have shape (4,4).")

        object_ = self.get_object(object_name)

        current_transform = object_.getTransform()
        current_transform_matrix = np.identity(4)
        current_transform_matrix[:3, :3] = current_transform.getRotation()
        current_transform_matrix[:3, 3] = current_transform.getTranslation()

        self.set_transform(object_name, transform_matrix @ current_transform_matrix)

    def get_object(self, object_name: str) -> fcl.CollisionObject:
        if not object_name in self._objs:
            raise KeyError(
                f"No object with name '{object_name}' in this collision manager.")

        return self._objs[object_name]["obj"]

    def merge(self, other_collision_manager: "CustomCollisionManager") -> None:
        for name, value in other_collision_manager._objs.items():    #pylint: disable=protected-access
            bvh = value["geom"]
            o = value["obj"]
            # Add collision object to set
            if name in self._objs:
                self._manager.unregisterObject(self._objs[name])
            self._objs[name] = value
            # store the name of the geometry
            self._names[id(bvh)] = name

            self._manager.registerObject(o)
            self._manager.update()
