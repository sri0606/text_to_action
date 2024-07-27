package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	// "reflect"
)

// Example functions
func addFunction(args map[string]interface{}) float64 {
	a := args["a"].(float64)
	b := args["b"].(float64)
	return a + b
}

func subtractFunction(args map[string]interface{}) float64 {
	a := args["a"].(float64)
	b := args["b"].(float64)
	return a - b
}

func multiplyFunction(args map[string]interface{}) float64 {
	a := args["a"].(float64)
	b := args["b"].(float64)
	return a * b
}

func divideFunction(args map[string]interface{}) float64 {
	a := args["a"].(float64)
	b := args["b"].(float64)
	return a / b
}

type operationFunc func(map[string]interface{}) float64

var functionMap = map[string]struct {
	function   operationFunc
	arguments  map[string]string
}{
	"add": {
		function: addFunction,
		arguments: map[string]string{
			"a": "float64",
			"b": "float64",
		},
	},
	"subtract": {
		function: subtractFunction,
		arguments: map[string]string{
			"a": "float64",
			"b": "float64",
		},
	},
	"multiply": {
		function: multiplyFunction,
		arguments: map[string]string{
			"a": "float64",
			"b": "float64",
		},
	},
	"divide": {
		function: divideFunction,
		arguments: map[string]string{
			"a": "float64",
			"b": "float64",
		},
	},

}

type FunctionExtractionRequest struct {
	Text      string `json:"text"`
	TopK      int    `json:"top_k"`
	Threshold float64 `json:"threshold"`
}

type ParameterExtractionRequest struct {
	Text              string                 `json:"text"`
	FunctionsArgsDict map[string]map[string]interface{} `json:"functions_args_dict"`
}

func extractFunctions(userInput string) []string {
	// Create the request payload
	requestBody := FunctionExtractionRequest{
		Text:      userInput,
		TopK:      1,
		Threshold: 0.45,
	}

	// Marshal the request payload to JSON
	requestBodyJson, err := json.Marshal(requestBody)
	if err != nil {
		fmt.Println("Error marshaling request body:", err)
		return nil
	}

	// Make the POST request
	response, err := http.Post("http://localhost:8000/extract_functions", "application/json", bytes.NewBuffer(requestBodyJson))
	if err != nil {
		fmt.Println("Error making POST request:", err)
		return nil
	}
	defer response.Body.Close()

	// Read and process the response body
	body, err := ioutil.ReadAll(response.Body)
	if err != nil {
		fmt.Println("Error reading response body:", err)
		return nil
	}

	// Print raw response body for debugging
	fmt.Println("Extracted functions:", string(body))

	// Unmarshal the response body into a slice of strings
	var functionsResponse []string
	if err := json.Unmarshal(body, &functionsResponse); err != nil {
		fmt.Println("Error unmarshaling response:", err)
		return nil
	}

	return functionsResponse
}

func extractArguments(userInput string, functionsArgsDict map[string]map[string]interface{}) map[string]interface{} {
	// Create the request payload
	requestBody := map[string]interface{}{
		"text":               userInput,
		"functions_args_dict": functionsArgsDict,
	}

	// Marshal the request payload to JSON
	requestBodyJson, err := json.Marshal(requestBody)
	if err != nil {
		fmt.Println("Error marshaling request body:", err)
		return nil
	}

	// Make the POST request
	response, err := http.Post("http://localhost:8000/extract_arguments", "application/json", bytes.NewBuffer(requestBodyJson))
	if err != nil {
		fmt.Println("Error making POST request:", err)
		return nil
	}
	defer response.Body.Close()

	// Read the response body
	body, err := ioutil.ReadAll(response.Body)
	if err != nil {
		fmt.Println("Error reading response body:", err)
		return nil
	}

	// Print raw response body for debugging
	fmt.Println("Extracted arguments:", string(body))

	// Unmarshal the JSON string response
	var argumentsResponse map[string]interface{}
	if err := json.Unmarshal(body, &argumentsResponse); err != nil {
		fmt.Println("Error unmarshaling response:", err)
		return nil
	}

	return argumentsResponse
}


func extractAndExecute(userInput string) {
	functions := extractFunctions(userInput)

	for _, funcName := range functions {
		funcInfo, ok := functionMap[funcName]
		if !ok {
			fmt.Printf("Function %s not found\n", funcName)
			continue
		}

		// Build the arguments map based on expected arguments
		functionArgs := make(map[string]interface{})
		for key, _ := range funcInfo.arguments {
			functionArgs[key] = nil // Initialize with `nil` or any default value
		}

		args := extractArguments(userInput, map[string]map[string]interface{}{
			funcName: functionArgs,
		})

		// Convert extracted arguments to a usable format
		argsMap, ok := args[funcName].(map[string]interface{})
		if !ok {
			fmt.Printf("Error converting arguments for %s\n", funcName)
			continue
		}

		// Assuming funcInfo.function accepts arguments as a map[string]interface{}
		result := funcInfo.function(argsMap)
		fmt.Printf("Result of %s: %f\n", funcName, result)
	}
}

func main() {
	userInputs := []string{
		"add 3 and 4",
		"subtract 5 from 10",
		"multiply 2 and 3",
		"divide 10 by 2",
	}

	for _, userInput := range userInputs {
		extractAndExecute(userInput)
		fmt.Println()
	}
}
