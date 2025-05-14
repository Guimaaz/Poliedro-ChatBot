// import React from 'react';
// import { createNativeStackNavigator } from '@react-navigation/native-stack';
// import LoginScreen from '../app/(tabs)/LoginScreen';
// import ChatbotScreen from '../app/(tabs)/chatbotScreen';
// import { NavigationContainer } from '@react-navigation/native';
// import { StackNavigationProp } from '@react-navigation/stack';

// const Stack = createNativeStackNavigator();

// type RootStackParamList = {
//   LoginScreen: undefined;
//   ChatbotScreen: undefined;
//   // Adicione outras telas e seus parâmetros aqui, por exemplo:
//   // Details: { itemId: number };
// };

// export type RootStackNavigationProp = StackNavigationProp<RootStackParamList>;

// const AppNavigator = () => {
//   return (
//     <NavigationContainer>
//       <Stack.Navigator>
//     <Stack.Screen
//   name="LoginScreen"
//   component={LoginScreen}
//   options={{ title: 'testeeee' }} // Ou o texto que você preferir
// />
//         <Stack.Screen name="ChatbotScreen" component={ChatbotScreen} />
//         {/* Adicione outras telas aqui */}
//       </Stack.Navigator>
//     </NavigationContainer>
//   );
// };

// export default AppNavigator;