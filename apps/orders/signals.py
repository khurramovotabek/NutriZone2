"""Signal handlers for the orders domain.

Phase 3 will likely add a post_save hook on OrderStatusHistory here (or a
signal fired from OrderService.change_status) to trigger notification tasks
when status changes -- not added yet since notifications/tasks don't exist.
"""
