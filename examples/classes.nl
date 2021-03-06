class Animal {
  /* gradual typing means this is "optional".  But the linter will warn */
  Str name
  Int age

  def __init__(self, Str name, Int age) {
    self.name = name
    self.age = age
  }

  def __str__(self) -> Str {
    return "an animal named {}".format(self.name)
  }

  def __repr__(self) -> Str {
    return "<Animal {:?}>".format(self.name)
  }
}

class Dog(Animal) {
  Bool is_barking

  def __init__(self, Str name, Int age) {
    Animal.__init__(self, name, age)
    self.is_barking = false
  }
}

def main() {
  var items = [ # dynamic typing
    Dog('Lumpi', 3),
    Dog('Joe', 7),
  ]

  for item in items {
    print("I have {}; it is {} years old", item, item.age)
  }
}
