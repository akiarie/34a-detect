package cmd

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"postproc/proc"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "postproc [results file path]",
	Short: "Obtain JSON details from the Azure output",
	Args: func(cmd *cobra.Command, args []string) error {
		if len(args) < 1 {
			return fmt.Errorf("requires path to Azure result file")
		}
		return nil
	},
	Run: func(cmd *cobra.Command, args []string) {
		data, err := os.ReadFile(args[0])
		if err != nil {
			log.Fatalf("cannot read file: %s\n", err)
		}
		form, err := proc.Parse34A(data)
		if err != nil {
			log.Fatalf("cannot process: %s\n", err)
		}
		b, err := json.Marshal(form)
		if err != nil {
			log.Fatalf("cannot marshal output: %s\n", err)
		}
		fmt.Println(string(b))
	},
}

func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}
