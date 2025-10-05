# Post-Reorganization Checklist

Use this checklist to verify everything works correctly after the reorganization.

---

## ✅ Immediate Verification (Already Done)

- [x] **Reorganization script executed successfully**
- [x] **All files copied to new structure**
- [x] **Import statements updated**
- [x] **Import tests passing**
  - [x] batch_timeseries
  - [x] single_image_analysis
  - [x] manual_bayer_processor
- [x] **Documentation created**

---

## 🧪 Testing Phase (Recommended)

### 1. GUI Application Tests

Test each application launches correctly:

```bash
# Batch Time-Series
cd batch_timeseries
python main.py
# ✓ Window opens
# ✓ All controls visible
# ✓ No error messages
```

```bash
# Single Image Analysis
cd single_image_analysis
python main.py
# ✓ Window opens
# ✓ All controls visible
# ✓ No error messages
```

```bash
# Manual Bayer Processor
cd manual_bayer_processor
python main.py
# ✓ Window opens
# ✓ All controls visible
# ✓ No error messages
```

**Checklist:**
- [ ] batch_timeseries GUI launches successfully
- [ ] single_image_analysis GUI launches successfully
- [ ] manual_bayer_processor GUI launches successfully

---

### 2. CLI Interface Tests

Test command-line interfaces:

```bash
# Batch Time-Series CLI
cd batch_timeseries
python cli.py --help
# ✓ Help text displays
# ✓ All arguments listed
```

```bash
# Single Image Analysis CLI
cd single_image_analysis
python cli.py --help
# ✓ Help text displays
# ✓ All arguments listed
```

**Checklist:**
- [ ] batch_timeseries CLI help works
- [ ] single_image_analysis CLI help works

---

### 3. ROI Selector Test (Shared Utility)

Test the shared ROI selector:

```bash
# Test from batch_timeseries
cd batch_timeseries
python main.py
# 1. Select a brightfield image
# 2. Click "选择ROI区域"
# 3. ✓ ROI selector window opens
# 4. ✓ Can draw ROI rectangle
# 5. ✓ ROI coordinates saved
```

**Checklist:**
- [ ] ROI selector opens from batch_timeseries
- [ ] ROI selector works correctly
- [ ] No import errors

---

### 4. Functional Tests

#### Batch Time-Series
```bash
cd batch_timeseries
python main.py

Test Workflow:
1. Select brightfield image
2. Select fluorescence folder
3. Optional: Select ROI
4. Click "开始处理"
5. ✓ Processing completes
6. ✓ CSV file generated
7. ✓ Overlay images created
8. ✓ Log file created
```

**Checklist:**
- [ ] Can select input files
- [ ] Processing runs without errors
- [ ] Output files generated correctly
- [ ] Results match old version

#### Single Image Analysis
```bash
cd single_image_analysis
python main.py

Test Workflow:
1. Select input image
2. Adjust parameters
3. Click "预览检测"
4. ✓ Preview shows detection
5. Click "处理"
6. ✓ CSV file generated
7. ✓ Overlay image created
```

**Checklist:**
- [ ] Can select input file
- [ ] Preview works
- [ ] Processing completes
- [ ] Output files correct

#### Manual Bayer Processor
```bash
cd manual_bayer_processor
python main.py

Test Workflow:
1. Load main image
2. Step through processing
3. ✓ Each step works
4. Save results
5. ✓ Output files created
```

**Checklist:**
- [ ] Image loading works
- [ ] All processing steps work
- [ ] Results can be saved

---

### 5. Configuration Tests

Test configuration save/load:

```bash
# Batch Time-Series
cd batch_timeseries
python main.py
# 1. Adjust parameters
# 2. Save configuration
# 3. Close application
# 4. Reopen
# 5. ✓ Configuration loaded
```

**Checklist:**
- [ ] Can save configuration
- [ ] Configuration persists
- [ ] Can load saved configuration

---

### 6. Test Suite Execution

Run existing test suites:

```bash
# Batch Time-Series Tests
cd batch_timeseries/tests
python test_app.py
# ✓ Tests pass
```

```bash
# Single Image Tests
cd single_image_analysis/tests
python test_processor.py
# ✓ Tests pass
```

```bash
# Manual Bayer Tests
cd manual_bayer_processor/tests
python run_tests.py
# ✓ Tests pass
```

**Checklist:**
- [ ] batch_timeseries tests pass
- [ ] single_image_analysis tests pass
- [ ] manual_bayer_processor tests pass

---

## 📊 Comparison with Old Version

### Output Verification

Process the same test data with both old and new versions:

**Test Data:**
- Brightfield image: `test_brightfield.tif`
- Fluorescence folder: `test_fluo/`

**Old Version:**
```bash
cd BatchFluoMeasurement
python batch_fluo_measurement.py
# Process test data
# Save results to: old_results/
```

**New Version:**
```bash
cd batch_timeseries
python main.py
# Process same test data
# Save results to: new_results/
```

**Compare:**
```bash
# Compare CSV files
diff old_results/results.csv new_results/results.csv

# Compare overlay images visually
```

**Checklist:**
- [ ] Results are identical or very similar
- [ ] Any differences are explainable
- [ ] No functionality lost

---

## 🧹 Cleanup Phase (After Complete Verification)

### ⚠️ ONLY AFTER ALL TESTS PASS

Once you've verified everything works:

1. **Back up old directories** (recommended):
```bash
cd ImageProcessor
mkdir _old_backup_20251005
mv BatchFluoMeasurement _old_backup_20251005/
mv FluoImagesSingleMeasurement _old_backup_20251005/
mv ManualFluoMeasurement _old_backup_20251005/
```

2. **Or delete old directories** (if confident):
```bash
# ⚠️ DANGER: Only if 100% sure everything works!
rm -rf BatchFluoMeasurement
rm -rf FluoImagesSingleMeasurement
rm -rf ManualFluoMeasurement
```

**Checklist:**
- [ ] All tests completed successfully
- [ ] Results verified against old version
- [ ] Old directories backed up or deleted
- [ ] Workspace clean

---

## 📝 Documentation Review

Ensure you've read:

- [ ] `README.md` - Overview of all projects
- [ ] `MIGRATION_GUIDE.md` - Understand the changes
- [ ] `QUICK_REFERENCE.md` - Know how to use tools
- [ ] `REORGANIZATION_COMPLETE.md` - Understand what was done
- [ ] `BEFORE_AFTER_COMPARISON.md` - See the improvements

---

## 🔧 Development Workflow Updates

Update your development practices:

### Running Applications
- [ ] Updated to use `cd <project> && python main.py`
- [ ] Know where each project is located
- [ ] Understand new import structure

### Adding Features
- [ ] Know to put business logic in `core/`
- [ ] Know to put UI code in `gui/`
- [ ] Know to put tests in `tests/`
- [ ] Know to use `shared_utils/` for common code

### Modifying Shared Code
- [ ] Understand that changes to `shared_utils/` affect all projects
- [ ] Know to test all projects after modifying shared code

---

## 📚 Knowledge Transfer

If working with a team:

- [ ] Share reorganization documents with team
- [ ] Update any external documentation
- [ ] Update CI/CD pipelines (if any)
- [ ] Update deployment scripts (if any)
- [ ] Train team members on new structure

---

## 🐛 Issue Reporting

If you find issues:

1. **Check documentation first**
   - `MIGRATION_GUIDE.md` for common issues
   - `QUICK_REFERENCE.md` for troubleshooting

2. **Check import paths**
   - Verify you're using `from core.` not just `from`
   - Check shared_utils path is correct

3. **Compare with old version**
   - Old directories are preserved for reference
   - Check if issue existed before

4. **Document the issue**
   - What you were doing
   - Error message
   - Expected vs actual behavior

---

## ✅ Final Verification

Before considering reorganization complete:

- [ ] All GUI applications launch successfully
- [ ] All CLI interfaces work
- [ ] ROI selector works (shared utility)
- [ ] Can process test data
- [ ] Results match old version
- [ ] All test suites pass
- [ ] Configuration save/load works
- [ ] Documentation reviewed
- [ ] Team informed (if applicable)
- [ ] Old directories handled (backed up or deleted)

---

## 🎉 Success Criteria

You can consider the reorganization successful when:

✅ All applications run without errors  
✅ All features work as before  
✅ Test suites pass  
✅ Results match old version  
✅ Team understands new structure  
✅ Documentation is clear  
✅ Workflow is smooth  

---

## 📞 Support Resources

If you need help:

1. **Documentation:**
   - `README.md` - Overview
   - `MIGRATION_GUIDE.md` - Migration help
   - `QUICK_REFERENCE.md` - Quick answers

2. **Code Reference:**
   - Old directories (if preserved) for comparison
   - `reorganize_projects.py` to see what was changed

3. **Testing:**
   - Run test suites to verify functionality
   - Process test data to compare results

---

## 🎊 Congratulations!

Once you complete this checklist, your code reorganization is fully verified and complete!

**Date:** 2025-10-05  
**Status:** Ready for verification

---

**Tip:** Work through this checklist systematically. Don't rush - thorough testing now saves debugging time later!
