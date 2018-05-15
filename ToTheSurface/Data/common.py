class FunctionList(list):
	def fire(self, *args, **kwargs):
		for funct in self:
			funct(*args, **kwargs)
