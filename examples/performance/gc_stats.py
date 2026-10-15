import gc

gc.collect()
print(gc.get_stats()[-1])
