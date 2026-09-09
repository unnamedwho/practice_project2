import Playgrounds

#Playground {
    // Step 1: Declare Variables for Personal Information
    var firstName: String = "Akerke"
    var lastName: String = "Zhumabekova"
    var birthYear: Int = 2006
    var currentYear: Int = 2026
    var age: Int = currentYear - birthYear
    var isStudent: Bool = true
    var height: Double = 1.75
    
    // Step 2: Create Variables for Your Hobbies and Interests
    var hobby: String = "reading"
    var currentBook: String = "Унесенные ветром"
    var numberOfHobbies: Int = 10
    var favoriteNumber: Int = 8
    var isHobbyCreative: Bool = true
    
    // Step 3: Create a Summary of Your Life Story
    let lifeStory: String = """
        My name is \(firstName) \(lastName). I am \(age) years old, i was born in \(birthYear). I am currently a student. My height is \(height). I love \(hobby), and now I am reading \(currentBook). I also have maybe like \(numberOfHobbies), which are travelling, dancing, painting, singing, and etc;) My favorite number is \(favoriteNumber). And it is \(isHobbyCreative) that my hobby is creative.
    
"""
    // Step 4: Print Your Life Story
    print(lifeStory)
}

