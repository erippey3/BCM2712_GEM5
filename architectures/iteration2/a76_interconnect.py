from m5.objects import L2XBar, L3XBar

class A76L2XBar(L2XBar):

    width = 32

    frontend_latency = 1

    forward_latency = 0

    response_latency = 1


class A76L3Xbar(L3XBar):
    width = 32

    frontend_latency = 1

    forward_latency = 0

    response_latency = 1



