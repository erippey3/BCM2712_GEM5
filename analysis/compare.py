from runtime_stats import RuntimeStats


def build_i1_fft():
    stats = RuntimeStats("iteration 1", "fft", "iteration 1 fft algorithm")

    stats.add_run("i1 fft", 1, 128, 0.000419)

    stats.add_run("i1 fft", 1, 256,  0.000429)

    stats.add_run("i1 fft", 1, 512, 0.000449)
                      
    stats.add_run("i1 fft", 1, 1024, 0.000493)
                      
    stats.add_run("i1 fft", 1, 2048, 0.000604)
                      
    stats.add_run("i1 fft", 1, 4096, 0.000904)
                      
    stats.add_run("i1 fft", 1, 8192, 0.001313)



    stats.add_run("i1 fft", 2, 128, 0.000496)
                      
    stats.add_run("i1 fft", 2, 256, 0.000503)
                      
    stats.add_run("i1 fft", 2, 512, 0.000516)
                      
    stats.add_run("i1 fft", 2, 1024, 0.000532)
                      
    stats.add_run("i1 fft", 2, 2048, 0.000596)
                      
    stats.add_run("i1 fft", 2, 4096, 0.000769)
                      
    stats.add_run("i1 fft", 2, 8192, 0.001028)
                      

                      
    stats.add_run("i1 fft", 3, 128, 0.000512)
                      
    stats.add_run("i1 fft", 3, 256, 0.000518)
                      
    stats.add_run("i1 fft", 3, 512, 0.000529)
                      
    stats.add_run("i1 fft", 3, 1024, 0.000533)
                      
    stats.add_run("i1 fft", 3, 2048, 0.000581)
                      
    stats.add_run("i1 fft", 3, 4096, 0.000711)
                      
    stats.add_run("i1 fft", 3, 8192, 0.000924)
                      


    stats.add_run("i1 fft", 4, 128, 0.000508)
                      
    stats.add_run("i1 fft", 4, 256, 0.000513)
                      
    stats.add_run("i1 fft", 4, 512, 0.000523)
                      
    stats.add_run("i1 fft", 4, 1024, 0.000527)
                      
    stats.add_run("i1 fft", 4, 2048, 0.000567)
                      
    stats.add_run("i1 fft", 4, 4096, 0.000671)
                      
    stats.add_run("i1 fft", 4, 8192, 0.000855)

    return stats


def build_i2_fft():
    stats = RuntimeStats("iteration 2", "fft", "iteration 1 fft algorithm")

    stats.add_run("i2 fft", 1, 128, 0.000399)

    stats.add_run("i2 fft", 1, 256,  0.000407)

    stats.add_run("i2 fft", 1, 512, 0.000429)
                      
    stats.add_run("i2 fft", 1, 1024, 0.000472)
                      
    stats.add_run("i2 fft", 1, 2048, 0.000583)
                      
    stats.add_run("i2 fft", 1, 4096, 0.000879)
                      
    stats.add_run("i2 fft", 1, 8192, 0.001224)



    stats.add_run("i2 fft", 2, 128, 0.000465)
                      
    stats.add_run("i2 fft", 2, 256, 0.000471)
                      
    stats.add_run("i2 fft", 2, 512, 0.000486)
                      
    stats.add_run("i2 fft", 2, 1024, 0.000498)
                      
    stats.add_run("i2 fft", 2, 2048, 0.000563)
                      
    stats.add_run("i2 fft", 2, 4096, 0.000737)
                      
    stats.add_run("i2 fft", 2, 8192, 0.000953)
                      

                      
    stats.add_run("i2 fft", 3, 128, 0.000482)
                      
    stats.add_run("i2 fft", 3, 256, 0.000486)
                      
    stats.add_run("i2 fft", 3, 512, 0.000498)
                      
    stats.add_run("i2 fft", 3, 1024, 0.000502)
                      
    stats.add_run("i2 fft", 3, 2048, 0.000550)
                      
    stats.add_run("i2 fft", 3, 4096, 0.000674)
                      
    stats.add_run("i2 fft", 3, 8192, 0.000856)
                      


    stats.add_run("i2 fft", 4, 128, 0.000478)
                      
    stats.add_run("i2 fft", 4, 256, 0.000482)
                      
    stats.add_run("i2 fft", 4, 512, 0.000492)
                      
    stats.add_run("i2 fft", 4, 1024, 0.000495)
                      
    stats.add_run("i2 fft", 4, 2048, 0.000532)
                      
    stats.add_run("i2 fft", 4, 4096, 0.000640)
                      
    stats.add_run("i2 fft", 4, 8192, 0.000798)

    return stats



def build_hardware_fft():
    stats = RuntimeStats("hardware", "fft", "iteration 1 fft algorithm")

    stats.add_run("hardware fft", 1, 128, 0.00035)

    stats.add_run("hardware fft", 1, 256,  0.00028)

    stats.add_run("hardware fft", 1, 512, 0.00031)
                      
    stats.add_run("hardware fft", 1, 1024, 0.00040)
                      
    stats.add_run("hardware fft", 1, 2048, 0.00049)
                      
    stats.add_run("hardware fft", 1, 4096, 0.00077)
                      
    stats.add_run("hardware fft", 1, 8192, 0.00107)



    stats.add_run("hardware fft", 2, 128, 0.00039)
                      
    stats.add_run("hardware fft", 2, 256, 0.00038)
                      
    stats.add_run("hardware fft", 2, 512, 0.00045)
                      
    stats.add_run("hardware fft", 2, 1024, 0.00045)
                      
    stats.add_run("hardware fft", 2, 2048, 0.00057)
                      
    stats.add_run("hardware fft", 2, 4096, 0.00066)
                      
    stats.add_run("hardware fft", 2, 8192, 0.00098)
                      

                      
    stats.add_run("hardware fft", 3, 128, 0.00043)
                      
    stats.add_run("hardware fft", 3, 256, 0.00042)
                      
    stats.add_run("hardware fft", 3, 512, 0.00044)
                      
    stats.add_run("hardware fft", 3, 1024, 0.00048)
                      
    stats.add_run("hardware fft", 3, 2048, 0.00051)
                      
    stats.add_run("hardware fft", 3, 4096, 0.00065)
                      
    stats.add_run("hardware fft", 3, 8192, 0.00087)
                      


    stats.add_run("hardware fft", 4, 128, 0.00043)
                      
    stats.add_run("hardware fft", 4, 256, 0.00042)
                      
    stats.add_run("hardware fft", 4, 512, 0.00044)
                      
    stats.add_run("hardware fft", 4, 1024, 0.00046)
                      
    stats.add_run("hardware fft", 4, 2048, 0.00051)
                      
    stats.add_run("hardware fft", 4, 4096, 0.00065)
                      
    stats.add_run("hardware fft", 4, 8192, 0.00107)

    return stats



build_i1_fft().plot_vs_problem_size()
build_i1_fft().plot_vs_threads()

build_i2_fft().plot_vs_problem_size()
build_i2_fft().plot_vs_threads()

build_hardware_fft().plot_vs_problem_size()
build_hardware_fft().plot_vs_threads()
