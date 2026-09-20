"""
Unit tests for handcrafted DoublyLinkedList and Node.
"""

from core.dll import DoublyLinkedList, Node


def test_empty_list():
    dll = DoublyLinkedList()
    assert dll.is_empty()
    assert dll.size == 0
    assert len(dll) == 0
    assert dll.pop_tail() is None


def test_append_front_and_pop_tail():
    dll = DoublyLinkedList()
    n1 = Node("k1", "v1")
    n2 = Node("k2", "v2")
    n3 = Node("k3", "v3")

    dll.append_front(n1)
    dll.append_front(n2)
    dll.append_front(n3)

    assert dll.size == 3
    assert not dll.is_empty()

    # Order from head to tail: n3, n2, n1
    # Tail pop should yield n1 (least recently used)
    popped1 = dll.pop_tail()
    assert popped1 is n1
    assert dll.size == 2

    popped2 = dll.pop_tail()
    assert popped2 is n2
    assert dll.size == 1

    popped3 = dll.pop_tail()
    assert popped3 is n3
    assert dll.size == 0
    assert dll.is_empty()
    assert dll.pop_tail() is None


def test_remove_arbitrary_node():
    dll = DoublyLinkedList()
    n1 = Node("k1", "v1")
    n2 = Node("k2", "v2")
    n3 = Node("k3", "v3")

    dll.append_front(n1)
    dll.append_front(n2)
    dll.append_front(n3)

    # Remove middle node n2
    dll.remove(n2)
    assert dll.size == 2

    # Remaining in order: n3, n1
    keys = [node.key for node in dll]
    assert keys == ["k3", "k1"]

    # Remove head-adjacent node n3
    dll.remove(n3)
    assert dll.size == 1
    assert [node.key for node in dll] == ["k1"]

    # Remove only remaining node n1
    dll.remove(n1)
    assert dll.size == 0
    assert dll.is_empty()


def test_node_expiration():
    n = Node("k", "v", expiry=100.0)
    assert not n.is_expired(current_time=99.9)
    assert n.is_expired(current_time=100.0)
    assert n.is_expired(current_time=105.0)

    n_no_expiry = Node("k2", "v2", expiry=None)
    assert not n_no_expiry.is_expired(current_time=999999.0)
