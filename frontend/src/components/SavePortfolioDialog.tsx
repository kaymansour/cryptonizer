"use client";

import { useState } from "react";
import { useUser } from "@clerk/nextjs";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Save, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { savePortfolio, SavePortfolioData } from "@/lib/api";

interface SavePortfolioDialogProps {
    portfolioData: SavePortfolioData;
    buttonText?: string;
    buttonVariant?: "default" | "outline" | "secondary" | "ghost" | "link" | "destructive";
    buttonClassName?: string;
}

export default function SavePortfolioDialog({
    portfolioData,
    buttonText = "Save Portfolio",
    buttonVariant = "default",
    buttonClassName = "",
}: SavePortfolioDialogProps) {
    const { user, isSignedIn } = useUser();
    const [open, setOpen] = useState(false);
    const [portfolioName, setPortfolioName] = useState("");
    const [saving, setSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<{
        type: "success" | "error" | null;
        message: string;
    }>({ type: null, message: "" });

    const handleSave = async () => {
        if (!isSignedIn || !user) {
            setSaveStatus({
                type: "error",
                message: "You must be signed in to save portfolios",
            });
            return;
        }

        if (!portfolioName.trim()) {
            setSaveStatus({
                type: "error",
                message: "Please enter a portfolio name",
            });
            return;
        }

        setSaving(true);
        setSaveStatus({ type: null, message: "" });

        try {
            const response = await savePortfolio(
                {
                    ...portfolioData,
                    name: portfolioName.trim(),
                },
                user.id
            );

            setSaveStatus({
                type: "success",
                message: `Portfolio "${portfolioName}" saved successfully!`,
            });

            // Clear the name and close after a short delay
            setTimeout(() => {
                setPortfolioName("");
                setOpen(false);
                setSaveStatus({ type: null, message: "" });
            }, 2000);
        } catch (error) {
            setSaveStatus({
                type: "error",
                message: error instanceof Error ? error.message : "Failed to save portfolio",
            });
        } finally {
            setSaving(false);
        }
    };

    const handleOpenChange = (newOpen: boolean) => {
        if (!newOpen) {
            // Reset state when closing
            setSaveStatus({ type: null, message: "" });
            setPortfolioName("");
        }
        setOpen(newOpen);
    };

    if (!isSignedIn) {
        return (
            <Button variant={buttonVariant} className={buttonClassName} disabled>
                <Save className="mr-2 h-4 w-4" />
                Sign in to Save
            </Button>
        );
    }

    return (
        <AlertDialog open={open} onOpenChange={handleOpenChange}>
            <AlertDialogTrigger asChild>
                <Button variant={buttonVariant} className={buttonClassName}>
                    <Save className="mr-2 h-4 w-4" />
                    {buttonText}
                </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="sm:max-w-[425px]">
                <AlertDialogHeader>
                    <AlertDialogTitle>Save Portfolio</AlertDialogTitle>
                    <AlertDialogDescription>
                        Give your portfolio a name to save it for later. You can view and manage all your saved
                        portfolios from your dashboard.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="name">Portfolio Name</Label>
                        <Input
                            id="name"
                            placeholder="e.g., My Balanced Crypto Portfolio"
                            value={portfolioName}
                            onChange={(e) => setPortfolioName(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !saving) {
                                    handleSave();
                                }
                            }}
                            disabled={saving}
                            className="col-span-3"
                        />
                    </div>

                    {/* Portfolio Summary */}
                    <div className="rounded-lg bg-muted p-3 space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">Assets:</span>
                            <span className="font-medium">{portfolioData.symbols.length} coins</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">Total Value:</span>
                            <span className="font-medium">
                                ${portfolioData.total_value.toLocaleString()}
                            </span>
                        </div>
                        {portfolioData.sharpe_ratio && (
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Sharpe Ratio:</span>
                                <span className="font-medium">{portfolioData.sharpe_ratio.toFixed(2)}</span>
                            </div>
                        )}
                        {portfolioData.expected_return && (
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Expected Return:</span>
                                <span className="font-medium text-green-600 dark:text-green-400">
                                    {(portfolioData.expected_return * 100).toFixed(2)}%
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Status Messages */}
                    {saveStatus.type && (
                        <div
                            className={`flex items-center gap-2 p-3 rounded-lg ${saveStatus.type === "success"
                                    ? "bg-green-500/10 text-green-600 dark:text-green-400"
                                    : "bg-red-500/10 text-red-600 dark:text-red-400"
                                }`}
                        >
                            {saveStatus.type === "success" ? (
                                <CheckCircle2 className="h-4 w-4" />
                            ) : (
                                <AlertCircle className="h-4 w-4" />
                            )}
                            <span className="text-sm">{saveStatus.message}</span>
                        </div>
                    )}
                </div>
                <AlertDialogFooter>
                    <AlertDialogCancel disabled={saving}>
                        Cancel
                    </AlertDialogCancel>
                    <Button
                        type="button"
                        onClick={handleSave}
                        disabled={saving || !portfolioName.trim()}
                    >
                        {saving ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Saving...
                            </>
                        ) : (
                            <>
                                <Save className="mr-2 h-4 w-4" />
                                Save Portfolio
                            </>
                        )}
                    </Button>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
