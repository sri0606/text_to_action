const axios = require('axios');

// Example functions
const addFunc = (a, b) => a + b;
const subtractFunc = (a, b) => a - b;
const multiplyFunc = (a, b) => a * b;
const divideFunc = (a, b) => a / b;

const functionMap = {
  "add": addFunc,
  "subtract": subtractFunc,
  "multiply": multiplyFunc,
  "divide": divideFunc,
};

function buildFunctionsArgsDict(func_obj, functionName) {
  const argsDict = {};
  const funcStr = func_obj.toString();
  const argsRegex = /\(([^)]+)\)/;
  const argsMatch = argsRegex.exec(funcStr);
  if (argsMatch) {
    const args = argsMatch[1].split(',').map(arg => arg.trim());
    args.forEach((arg, index) => {
      argsDict[arg] = "int";
    });
  }
  return {[functionName]: argsDict};
}


async function extractAndExecute(userInput, functionMap) {
  try {
    // Extract functions
    const extractFunctionsResponse = await axios.post('http://localhost:8000/extract_functions', {
        text: userInput,
        top_k: 1,
        threshold: 0.45,
      },
    );

    const extractedFunctions = extractFunctionsResponse.data;
    console.log('Functions extraction response:', extractedFunctions);

    // Extract arguments and execute each function
    for (const functionName of extractedFunctions) {
      if (functionMap[functionName]) {
        await extractArgumentsAndExecute(userInput, functionName, functionMap[functionName]);
      } else {
        console.log(`Function ${functionName} not found in functionMap`);
      }
    }
  } catch (error) {
    console.error('Error in extractAndExecute:', error);
  }
}

async function extractArgumentsAndExecute(userInput, functionName,func_obj) {
  const functionsArgsDict = buildFunctionsArgsDict(func_obj, functionName);
  
  console.log(`Extracting arguments for ${functionName}...`);
  console.log("function arguments dict:", functionsArgsDict);

  try {
    const extractArgumentsResponse = await axios.post('http://localhost:8000/extract_arguments', {
      text: userInput,
      functions_args_dict:  JSON.stringify(functionsArgsDict),
    });

    const extractedArguments = JSON.parse(extractArgumentsResponse.data);
    console.log(`Arguments extraction response for ${functionName}:`, extractedArguments);

     // Execute the function with the extracted arguments
     const args = Object.values(extractedArguments[functionName]).map(arg => parseFloat(arg));
     if (args.some(isNaN)) {
       console.error(`Error in extractArgumentsAndExecute for ${functionName}: Invalid argument values`);
     } else {
       const result = func_obj(...args);
       console.log(`Result of ${functionName}:`, result);
     }
   } catch (error) {
     console.error(`Error in extractArgumentsAndExecute for ${functionName}:`, error);
   }
 }

// Example usage
const userInputs = ['add 3 and 4','subtract 2 from 1','multiply 5 and 6','divide 8, 2'];

for (const input of userInputs) {
  extractAndExecute(input, functionMap);
}
