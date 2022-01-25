friends = ['Emelia', 'Jack', 'Bernardina', 'Jaap']

while True:
    name = input('What is your name?\n')
    
    if name in friends:
        print(f'Hello, {name}!')
    else:
        print("I don't know you.")
        friends.append(name)
