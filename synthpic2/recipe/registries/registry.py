"""Registry for recipe components."""

from typing import Any, Iterator, List, Optional, Union

from ...errors import ConventionError

Index = Union[str, int]


class Registry:
    """Registry for objects."""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name
        self.items: List[Any] = []

    def clear(self) -> None:
        self.items.clear()

    def register(self, item: Any) -> None:
        """Register a new item.

        Args:
            item (Any): item to be registered
        """
        self.validate(item)
        self.items.append(item)

    def validate(self, item: Any) -> None:
        """Validate a new item.

        Args:
            item (Any): item to be validated
        """

        if not hasattr(item, "name"):
            raise AttributeError(
                "This registry expects items to have a `name` attribute.")

        previous_item_names = [i.name for i in self.items]
        if item.name in previous_item_names:
            raise ConventionError(
                f"There already exists an item with name '{item.name}' in this "
                f"registry.")

        # ? TODO: Re-enable this check? Results in an exception, if objects only have a
        #   common super class.
        # if len(self) > 0:
        #     if not isinstance(item, type(self.items[0])):
        #         raise TypeError(
        #             f"Expected item to be of the same type as the previous items in "
        #             f"this registry ('{type(self.items[0])}').")

    def query(self, name: Optional[Index], strict: bool = False) -> Any:
        """Return an item with a given name from the registry.

        Args:
            name (Index): name or integer index of the desired item, optional
            strict (bool): if True, then an error will be raised if the item is not
                found in the registry

        Returns:
            Optional[_Prototype]: Item or `None`, if the item does not exist in the
                registry.
        """

        item = self.__getitem__(name)

        if strict and item is None:
            raise KeyError(f"Could not find item '{name}' in registry '{self.name}'.")

        return item

    def delete_item(self, index: Index) -> None:
        if isinstance(index, str):
            self.items = [item for item in self.items if item.name != index]

        if isinstance(index, int):
            try:
                del self.items[index]
            except IndexError:
                pass

    def __iter__(self) -> Iterator:
        return iter(self.items)

    def __next__(self) -> Any:
        return next(iter(self.items))

    def __getitem__(self, index: Optional[Index]) -> Any:
        if index is None:
            return None

        if isinstance(index, str):
            for item in self.items:
                if item.name == index:
                    return item

        if isinstance(index, int):
            try:
                return self.items[index]
            except IndexError:
                pass

        return None

    def __len__(self) -> int:
        return len(self.items)

    def __contains__(self, name: str) -> bool:
        return self[name] is not None
