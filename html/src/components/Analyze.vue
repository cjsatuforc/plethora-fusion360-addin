<template>
  <div class="analyze">
    <div v-if="analysis === null">
      <h1>{{ analyzing ? "ANALYZING..." : "START ANALYSIS" }}</h1>
      <p v-if="!analyzing">Run manufacturability checks and receive instant feedback.</p>
      <div v-if="errorMessage !== ''" class="alert">
        <p>{{ errorMessage }}</p>
      </div>
      <p v-if="!analyzing">Select a Material</p>
      <dropdown v-if="!analyzing" :close-on-click="true">
        <template slot="btn">{{selectedMaterial !== null ? selectedMaterial.description : ""}}</template>
        <template slot="body">
            <div v-on:click="selectMaterial(material)" v-for="material in materials" v-bind:key="material.id">
                {{ material.description }}
            </div>
        </template>
        <template slot="icon">
          <img src="../assets/caret.svg" />
        </template>
      </dropdown>
      <button class="plethora-button" v-if="!analyzing" type="button" v-on:click="analyze()">
        Analyze
        <img src="../assets/arrow-cta.svg" />
      </button>
      <vue-simple-spinner v-if="analyzing" size="medium" line-fg-color="#51ca7a"></vue-simple-spinner>
    </div>
    <div v-if="analysis !== null">
      <div v-if="analysisSuccessful">
        <h1>SUCCESS!</h1>
        <p>Your part passed - finalize the options below for instant checkout.</p>
        <p>Quantity</p>
        <dropdown :close-on-click="true">
          <template slot="btn">{{selectedQuantity}}</template>
          <template slot="body">
              <div v-on:click="updateQuantity(quantity)" v-for="quantity in [1,2,3,4,5]" v-bind:key="quantity">
                  {{ quantity }}
              </div>
          </template>
          <template slot="icon">
            <img src="../assets/caret.svg" />
          </template>
        </dropdown>
        <p>Ship Date</p>
        <dropdown :class-name="'ship-date'" :close-on-click="true">
          <template slot="btn">{{turnaroundDateString(selectedTurnaround)}}</template>
          <template slot="body">
              <div v-on:click="updateTurnaround(turnaround)" v-for="turnaround in analysis['turnarounds'
              ]" v-bind:key="turnaround['days']">
                  {{ turnaroundDateString(turnaround) }}
              </div>
          </template>
          <template slot="icon">
            <img src="../assets/caret.svg" />
          </template>
        </dropdown>
        <p>Total</p>
        <p>${{ parseFloat(total).toFixed(2) }}</p>
        <button class="plethora-button" v-if="!analyzing" type="button" v-on:click="checkOut()">
          Check Out
          <img src="../assets/arrow-cta.svg" />
        </button>
        <button class="plethora-button" v-if="!analyzing" type="button" v-on:click="analyze()">
          Re-Analyze
          <img src="../assets/arrow-cta.svg" />
        </button>
        <a href="#" v-on:click="startOver()">Select a different material</a>
      </div>
      <div v-else>
        <h1>FEEDBACK</h1>
        <p>Address these issues to get an instant quote.</p>
        <div class="plethora-issue" v-for="issue in getIssues()" v-bind:key="issue['faces'][0]">
          <p class="plethora-issue-name">{{ issue['name'] }}</p>
          <p class="plethora-issue-description">{{ issue['description'] }}</p>
        </div>
        <button class="plethora-button" v-if="!analyzing" type="button" v-on:click="analyze()">
          Re-Analyze
          <img src="../assets/arrow-cta.svg" />
        </button>
        <a href="#" v-on:click="startOver()">Select a different material</a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Analyze",
  data: function() {
    return {
      errorMessage: "",
      analyzing: false,
      materials: [],
      selectedMaterial: null,
      analysis: null,
      analysisSuccessful: false,
      selectedQuantity: 1,
      selectedTurnaround: null,
      total: 0.0
    };
  },
  mounted() {
    this.$eventBus.$on("analyze", data => {
      this.analyzing = false;

      if (data.data) {
        this.analysis = data.data;
        this.selectedTurnaround = this.analysis["turnarounds"][0];
        this.checkAnalysis();
      } else if (data.error) {
        this.errorMessage = data.error;
      }
    });

    this.$eventBus.$on("materials", data => {
      if (data.data) {
        this.materials = data.data;

        this.materials.sort(function(a, b) {
          return a.id > b.id;
        });

        this.selectedMaterial = this.materials[0];
      } else if (data.error) {
        this.errorMessage = data.error;
      }
    });

    this.getMaterials();
  },
  methods: {
    analyze: function() {
      if (this.selectedMaterial == null) {
        this.errorMessage =
          "You must select a material before analyzing your part";
        return;
      }

      this.errorMessage = "";
      this.analysis = null;
      this.analyzing = true;

      if (typeof adsk !== "undefined") {
        // eslint-disable-next-line
        adsk.fusionSendData("analyze", JSON.stringify(this.selectedMaterial));
      } else {
        setTimeout(() => {
          this.$eventBus.$emit("analyze", {
            data: mockedAnalysis,
            error: null
          });
        }, 2000);
      }
    },
    selectMaterial: function(material) {
      this.selectedMaterial = material;
    },
    getMaterials() {
      if (typeof adsk !== "undefined") {
        // eslint-disable-next-line
        adsk.fusionSendData("materials", JSON.stringify({}));
      } else {
        this.$eventBus.$emit("materials", {
          data: mockedMaterials,
          error: null
        });
      }
    },
    checkAnalysis() {
      this.analysisSuccessful = this.analysis["analysis"]["results"].reduce(
        (accumulator, currentValue) => {
          return accumulator && currentValue["status"] === "Success";
        },
        true
      );
      if (this.analysisSuccessful) {
        this.updateTotal();
      }
    },
    getIssues() {
      return this.analysis["analysis"]["results"].filter(el => {
        return el["status"] === "Error";
      });
    },
    turnaroundDateString(turnaround) {
      var year = turnaround["date"][0].toString();
      var month = turnaround["date"][1].toString();
      var day = turnaround["date"][2].toString();
      return month + "/" + day + "/" + year;
    },
    updateQuantity: function(quantity) {
      this.selectedQuantity = quantity;
      this.updateTotal();
    },
    updateTurnaround: function(turnaround) {
      this.selectedTurnaround = turnaround;
      this.updateTotal();
    },
    updateTotal() {
      this.total = this.getTotal();
    },
    getTotalTime: function() {
      var quote = this.analysis["analysis"]["quote"];
      var roughingTime = quote["roughing_time"];
      var facingTime = quote["facing_time"];
      var contourEdgesTime = quote["contour_edges_time"];
      // var contouredSurfacesTime = quote["contoured_surfaces_time"];
      var filletingTime = quote["filleting_time"];
      // var chamferingTime = quote["chamfering_time"];
      var drillingTime = quote["drilling_time"];
      var boringTime = quote["boring_time"];
      var countersinkingTime = quote["countersinking_time"];
      var threadingTime = quote["threading_time"];
      return (
        roughingTime +
        facingTime +
        contourEdgesTime +
        filletingTime +
        drillingTime +
        boringTime +
        countersinkingTime +
        threadingTime
      );
    },
    getPartCost: function() {
      var quote = this.analysis["analysis"]["quote"];
      var quoting = this.analysis["quoting"];

      var satelliteOrientations = quote["satellite_orientations"];
      var stockVolume = quote["stock_volume"];

      var materialCostPerVolume = quoting["material_cost_per_volume"];
      var materialCostPaddingFactor = quoting["material_cost_padding_factor"];
      var machineCostCoeff = quoting["machine_cost_coeff"];
      var manualSetupTimePerInstance =
        quoting["manual_setup_time_per_instance"];
      var labourCostPerSecond = quoting["labour_cost_per_second"];
      var setupCostPerSideApproach = quoting["setup_cost_per_side_approach"];

      var materialCost =
        stockVolume * materialCostPerVolume * materialCostPaddingFactor;
      var machineCost = this.getTotalTime() * machineCostCoeff;
      var manualSetupCost = manualSetupTimePerInstance * labourCostPerSecond;
      var sidesSetupCost = satelliteOrientations * setupCostPerSideApproach;
      var cost = machineCost + manualSetupCost + materialCost + sidesSetupCost;
      return this.precisionRound(cost, 2);
    },
    getSetupCost: function() {
      var quote = this.analysis["analysis"]["quote"];
      var quoting = this.analysis["quoting"];
      var setupTimePerPart = quoting["setup_time_per_part"];
      var satelliteOrientations = quote["satellite_orientations"];
      var labourCostPerSecond = quoting["labour_cost_per_second"];
      var camTimePerSatelliteOp = quoting["cam_time_per_satellite_op"];
      var camTimePerMachineTime = quoting["cam_time_per_machine_time"];
      var cost =
        setupTimePerPart * labourCostPerSecond +
        this.getTotalTime() * camTimePerMachineTime * labourCostPerSecond +
        camTimePerSatelliteOp * satelliteOrientations * labourCostPerSecond;
      return this.precisionRound(cost, 2);
    },
    getTotal: function() {
      return this.precisionRound(
        (this.getSetupCost() + this.selectedQuantity * this.getPartCost()) *
          this.selectedTurnaround["multiplier"],
        2
      );
    },
    checkOut: function() {
      if (typeof adsk !== "undefined") {
        var args = {
          setup_cost: this.getSetupCost(),
          part_cost: this.getPartCost(),
          turnaround_time: this.selectedTurnaround["days"],
          quantity: this.selectedQuantity
        };
        // eslint-disable-next-line
        adsk.fusionSendData("checkout", JSON.stringify(args));
      }
    },
    precisionRound: function(number, precision) {
      var factor = Math.pow(10, precision);
      return Math.round(number * factor) / factor;
    },
    startOver: function() {
      this.analyzing = false;
      this.analysis = null;
      this.errorMessage = "";
    }
  }
};

var mockedMaterials = [
  {
    id: 1,
    name: "alu6061",
    description: "6061 Aluminum",
    created_at: "2014-02-26T20:10:18.480Z",
    updated_at: "2018-05-26T08:00:23.446Z",
    title: "AL6061",
    price_per_cc: 0.025,
    material_class: "aluminum",
    standard_tolerance: 0.005,
    detail: {
      alias_rules: null,
      alias_stock: null,
      lead_time_pad: 0,
      cutting_parameters: {
        tap: {
          sfm: 80,
          chip_load_per_diameter: 0.175
        },
        drill: {
          sfm: 300,
          chip_load_per_diameter: 0.012
        },
        reamer: {
          sfm: 150,
          chip_load_per_diameter: 0.024
        },
        spot_drill: {
          sfm: 300,
          chip_load_per_diameter: 0.016
        },
        chamfer_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        ball_end_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        dovetail_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        flat_end_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        bull_nose_end_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        }
      },
      cutting_speed_factor: 1
    },
    status: "standard",
    plex_record_key: "30059",
    pretty_material_class: "Aluminum Alloys",
    enabled: true,
    _type: "materials"
  },
  {
    id: 2,
    name: "alu7075",
    description: "7075 Aluminum",
    created_at: "2014-02-26T20:10:18.480Z",
    updated_at: "2018-05-26T08:00:23.446Z",
    title: "AL7075",
    price_per_cc: 0.05,
    material_class: "aluminum",
    standard_tolerance: 0.005,
    detail: {
      alias_rules: null,
      alias_stock: null,
      lead_time_pad: 2,
      cutting_parameters: {
        tap: {
          sfm: 80,
          chip_load_per_diameter: 0.175
        },
        drill: {
          sfm: 300,
          chip_load_per_diameter: 0.012
        },
        reamer: {
          sfm: 150,
          chip_load_per_diameter: 0.024
        },
        spot_drill: {
          sfm: 300,
          chip_load_per_diameter: 0.016
        },
        chamfer_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        ball_end_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        dovetail_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        flat_end_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        },
        bull_nose_end_mill: {
          sfm: 2000,
          chip_load_per_diameter: 0.0068
        }
      },
      cutting_speed_factor: 0.9
    },
    status: "standard",
    plex_record_key: "30060",
    pretty_material_class: "Aluminum Alloys",
    enabled: true,
    _type: "materials"
  }
];

var mockedAnalysis = {
  quoting: {
    max_side_approaches_for_quoting: 3,
    chamfer_depth_per_pass: 1.11,
    tapping_intercept_coeff: 15,
    material_cost_per_volume: 0.025,
    drilling_coeff_b: 0.9844,
    roughing_material_slope_coeff: 3.5247314589117367,
    internal_fillet_slope_coeff_l: 10.73228346456693,
    interpolated_chamfer_intercept_coeff: 52.333,
    chamfer_intercept_coeff: 16.07,
    facing_material_slope_coeff: 1.548,
    stock_xy_padding: 0.254,
    drilling_material_coeff: 1,
    facing_material_intercept_coeff: 12.03,
    external_fillet_slope_coeff_r: 74.88188976377953,
    spot_drilling_material_intercept_coeff: 14,
    cam_time_per_machine_time: 2,
    contoured_faces_intercept_coeff: 32.01,
    machine_cost_coeff: 0.006111111111111111,
    interpolated_chamfer_slope_coeff_angle: 16.855,
    setup_time_per_part: 2400,
    drilling_coeff_c: 0.0447,
    external_fillet_slope_coeff_l: 23.846456692913385,
    countersink_intercept_coeff: 15,
    internal_fillet_slope_coeff_r: 131.29921259842519,
    material_cost_padding_factor: 1,
    stock_z_padding: 0.3175,
    spot_drilling_material_slope_coeff: 3.5,
    facing_step_down_depth: 0.1,
    cam_time_per_satellite_op: 900,
    manual_setup_time_per_instance: 300,
    not_interpolated_fillet_intercept_coeff: 15.4,
    roughing_material_intercept_coeff: 195.9,
    interpolated_chamfer_slope_coeff_depth: 4.913385826771654,
    internal_fillet_intercept_coeff: 43.27,
    not_interpolated_fillet_slope_coeff: 0.7874015748031495,
    interpolated_chamfer_slope_coeff_lenght: 17.716535433070867,
    drilling_coeff_a: 17.9788,
    setup_cost_per_side_approach: 10,
    contoured_edges_slope_coeff: 16.0833,
    standard_tolerance_in: 0.005,
    facing_number_step_downs: 2,
    contoured_edges_intercept_coeff: 22.72,
    labour_cost_per_second: 0.006944444444444444,
    external_fillet_intercept_coeff: 15.4,
    all_faces_require_milled_finish: true,
    chamfer_slope_coeff: 0.6692913385826771,
    contoured_faces_slope_coeff: 188.60999999999999
  },
  analysis: {
    material: "alu6061",
    stock_suggestion: {
      thickness: 2.54,
      width: 3.81,
      cut_length: 5.207985385991463
    },
    dimensions: [1.4000000000000004, 2.4983910589343035, 4.699985385991463],
    results: [
      {
        name: "Milled Through Hole",
        description: "This hole has 0.827in diameter and 0.541in depth. ",
        type: "HoleMilledThrough",
        status: "Success",
        faces: ["3122162317"]
      },
      {
        name: "Milled Through Hole",
        description: "This hole has 0.795in diameter and 0.541in depth. ",
        type: "HoleMilledThrough",
        status: "Success",
        faces: ["1061577058"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["2894583680"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["2032353091"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["582066122"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["694168702"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["594410109"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["1656885573"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["141886140"]
      },
      {
        name: "Ball Mill Interpolated",
        description: "Faces will be interpolated with a ball mill. ",
        type: "BallMillInterpolated",
        status: "Success",
        faces: ["3378096722"]
      },
      {
        name: "Facing Operation",
        description: "These surfaces will be faced by a mill. ",
        type: "FacedContour",
        status: "Success",
        faces: ["4186317286"]
      },
      {
        name: "Facing Operation",
        description: "These surfaces will be faced by a mill. ",
        type: "FacedContour",
        status: "Success",
        faces: ["562092228"]
      },
      {
        name: "Edge Finishing Operation",
        description: "These surfaces will be side cut using an end mill. ",
        type: "EdgeFinishedContour",
        status: "Success",
        faces: ["4229012251"]
      },
      {
        name: "Edge Finishing Operation",
        description: "These surfaces will be side cut using an end mill. ",
        type: "EdgeFinishedContour",
        status: "Success",
        faces: ["3351853726"]
      },
      {
        name: "Edge Finishing Operation",
        description: "These surfaces will be side cut using an end mill. ",
        type: "EdgeFinishedContour",
        status: "Success",
        faces: ["1530579349"]
      },
      {
        name: "Edge Finishing Operation",
        description: "These surfaces will be side cut using an end mill. ",
        type: "EdgeFinishedContour",
        status: "Success",
        faces: ["2278847483"]
      },
      {
        name: "Edge Finishing Operation",
        description: "These surfaces will be side cut using an end mill. ",
        type: "EdgeFinishedContour",
        status: "Success",
        faces: ["1813578744"]
      },
      {
        name: "Edge Finishing Operation",
        description: "These surfaces will be side cut using an end mill. ",
        type: "EdgeFinishedContour",
        status: "Success",
        faces: ["3347635337"]
      },
      {
        name: "Facing Operation",
        description: "These surfaces will be faced by a mill. ",
        type: "FacedContour",
        status: "Success",
        faces: ["1655773499"]
      },
      {
        name: "Edge Finishing Operation",
        description: "These surfaces will be side cut using an end mill. ",
        type: "EdgeFinishedContour",
        status: "Success",
        faces: ["2265275713"]
      },
      {
        name: "Part Size",
        description:
          "Stock of thickness 1in and width 1.5in is available for this part. ",
        type: "StockAvailable",
        status: "Success",
        faces: []
      }
      // {
      //   name: "Invalid Surface Type",
      //   description:
      //     "We can’t price this curved surface automatically. If the feature is required, please submit your part for a quote. ",
      //   type: "ContainsNonExtrudedBSplineSurface",
      //   status: "Error",
      //   faces: ["617983939"]
      // }
    ],
    quote: {
      roughing_time: 362.54653330612246,
      facing_time: 60.42669434043254,
      contour_edges_time: 51.87332,
      contoured_surfaces_time: 65.9061,
      filleting_time: 316.7636783837745,
      chamfering_time: 0,
      drilling_time: 0,
      boring_time: 259.753020051152,
      countersinking_time: 0,
      counterboring_time: 0,
      threading_time: 0,
      satellite_orientations: 0,
      stock_volume: 50.3997577743938
    },
    features: {
      holes: {
        count: 2,
        face_count: 2,
        surface_area: 10.093110574735164
      },
      pockets: { count: 0, face_count: 0, surface_area: 0 },
      inside_corners: {
        count: 3,
        face_count: 6,
        surface_area: 16.15030563164875
      },
      fillets: {
        count: 8,
        face_count: 8,
        surface_area: 1.2781513878657709
      },
      chamfers: { count: 0, face_count: 0, surface_area: 0 },
      side_milled: {
        count: 0,
        face_count: 7,
        surface_area: 14.17528031027509
      },
      face_milled: {
        count: 0,
        face_count: 3,
        surface_area: 6.371702576401582
      }
    }
  },
  turnarounds: [
    {
      parts_due_today: 19,
      max_quantity: 100,
      apple: {
        instances_due_today: 91,
        part_slots_available: 3,
        parts_due_today: 19,
        instance_slots_available: 0
      },
      instances_due_today: 91,
      max_mango_quantity: 100,
      date: [2018, 6, 1],
      mango: {
        instances_due_today: 91,
        part_slots_available: 3,
        parts_due_today: 19,
        instance_slots_available: 0
      },
      instance_slots_available: 0,
      max_apple_quantity: 100,
      days: 3,
      multiplier: 2.4,
      part_slots_available: 3,
      max_instance_slots: 102
    },
    {
      parts_due_today: 2,
      max_quantity: 100,
      apple: {
        instances_due_today: 13,
        part_slots_available: 41,
        parts_due_today: 2,
        instance_slots_available: 90
      },
      instances_due_today: 13,
      max_mango_quantity: 100,
      date: [2018, 6, 4],
      mango: {
        instances_due_today: 13,
        part_slots_available: 41,
        parts_due_today: 2,
        instance_slots_available: 90
      },
      instance_slots_available: 90,
      max_apple_quantity: 100,
      days: 4,
      multiplier: 2.2127868620911415,
      part_slots_available: 41,
      max_instance_slots: 102
    },
    {
      parts_due_today: 1,
      max_quantity: 258,
      apple: {
        instances_due_today: 1,
        part_slots_available: 44,
        parts_due_today: 1,
        instance_slots_available: 98
      },
      instances_due_today: 1,
      max_mango_quantity: 258,
      date: [2018, 6, 5],
      mango: {
        instances_due_today: 1,
        part_slots_available: 44,
        parts_due_today: 1,
        instance_slots_available: 98
      },
      instance_slots_available: 98,
      max_apple_quantity: 258,
      days: 5,
      multiplier: 2.1032741967721207,
      part_slots_available: 44,
      max_instance_slots: 260
    },
    {
      parts_due_today: 0,
      max_quantity: 248,
      apple: {
        instances_due_today: 0,
        part_slots_available: 60,
        parts_due_today: 0,
        instance_slots_available: 200
      },
      instances_due_today: 0,
      max_mango_quantity: 248,
      date: [2018, 6, 6],
      mango: {
        instances_due_today: 0,
        part_slots_available: 60,
        parts_due_today: 0,
        instance_slots_available: 200
      },
      instance_slots_available: 200,
      max_apple_quantity: 248,
      days: 6,
      multiplier: 2.025573724182283,
      part_slots_available: 60,
      max_instance_slots: 250
    },
    {
      parts_due_today: 2,
      max_quantity: 248,
      apple: {
        instances_due_today: 8,
        part_slots_available: 58,
        parts_due_today: 2,
        instance_slots_available: 192
      },
      instances_due_today: 8,
      max_mango_quantity: 248,
      date: [2018, 6, 7],
      mango: {
        instances_due_today: 8,
        part_slots_available: 58,
        parts_due_today: 2,
        instance_slots_available: 192
      },
      instance_slots_available: 192,
      max_apple_quantity: 248,
      days: 7,
      multiplier: 1.9653045553573991,
      part_slots_available: 58,
      max_instance_slots: 250
    },
    {
      parts_due_today: 7,
      max_quantity: 100,
      apple: {
        instances_due_today: 30,
        part_slots_available: 33,
        parts_due_today: 7,
        instance_slots_available: 60
      },
      instances_due_today: 30,
      max_mango_quantity: 100,
      date: [2018, 6, 8],
      mango: {
        instances_due_today: 30,
        part_slots_available: 33,
        parts_due_today: 7,
        instance_slots_available: 60
      },
      instance_slots_available: 60,
      max_apple_quantity: 100,
      days: 8,
      multiplier: 1.9160610588632623,
      part_slots_available: 33,
      max_instance_slots: 102
    },
    {
      parts_due_today: 1,
      max_quantity: 100,
      apple: {
        instances_due_today: 4,
        part_slots_available: 45,
        parts_due_today: 1,
        instance_slots_available: 96
      },
      instances_due_today: 4,
      max_mango_quantity: 100,
      date: [2018, 6, 11],
      mango: {
        instances_due_today: 4,
        part_slots_available: 45,
        parts_due_today: 1,
        instance_slots_available: 96
      },
      instance_slots_available: 96,
      max_apple_quantity: 100,
      days: 9,
      multiplier: 1.874426275817717,
      part_slots_available: 45,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 12],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 10,
      multiplier: 1.8383605862734242,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 13],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 11,
      multiplier: 1.8065483935442417,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 14],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 12,
      multiplier: 1.7780914174485405,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 15],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 13,
      multiplier: 1.75234895129379,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 18],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 14,
      multiplier: 1.7288479209544039,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 19],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 15,
      multiplier: 1.7072290687242342,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 20],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 16,
      multiplier: 1.6872131379088584,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 1,
      max_quantity: 100,
      apple: {
        instances_due_today: 4,
        part_slots_available: 45,
        parts_due_today: 1,
        instance_slots_available: 96
      },
      instances_due_today: 4,
      max_mango_quantity: 100,
      date: [2018, 6, 21],
      mango: {
        instances_due_today: 4,
        part_slots_available: 45,
        parts_due_today: 1,
        instance_slots_available: 96
      },
      instance_slots_available: 96,
      max_apple_quantity: 100,
      days: 17,
      multiplier: 1.6685787521295201,
      part_slots_available: 45,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 22],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 18,
      multiplier: 1.6511474483645658,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 25],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 19,
      multiplier: 1.6347732554036656,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 26],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 20,
      multiplier: 1.6193352556353835,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 6, 27],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 21,
      multiplier: 1.6047321605988516,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 1,
      max_quantity: 100,
      apple: {
        instances_due_today: 1,
        part_slots_available: 46,
        parts_due_today: 1,
        instance_slots_available: 98
      },
      instances_due_today: 1,
      max_mango_quantity: 100,
      date: [2018, 6, 28],
      mango: {
        instances_due_today: 1,
        part_slots_available: 46,
        parts_due_today: 1,
        instance_slots_available: 98
      },
      instance_slots_available: 98,
      max_apple_quantity: 100,
      days: 22,
      multiplier: 1.590878279539682,
      part_slots_available: 46,
      max_instance_slots: 102
    },
    {
      parts_due_today: 2,
      max_quantity: 100,
      apple: {
        instances_due_today: 24,
        part_slots_available: 42,
        parts_due_today: 2,
        instance_slots_available: 72
      },
      instances_due_today: 24,
      max_mango_quantity: 100,
      date: [2018, 6, 29],
      mango: {
        instances_due_today: 24,
        part_slots_available: 42,
        parts_due_today: 2,
        instance_slots_available: 72
      },
      instance_slots_available: 72,
      max_apple_quantity: 100,
      days: 23,
      multiplier: 1.577700472589838,
      part_slots_available: 42,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 7, 2],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 24,
      multiplier: 1.5651358133849316,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 7, 3],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 25,
      multiplier: 1.5531297716814327,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 7, 5],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 26,
      multiplier: 1.5416347830455455,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 7, 6],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 27,
      multiplier: 1.5306091107147983,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 7, 9],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 28,
      multiplier: 1.5200159308153756,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 7, 10],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 29,
      multiplier: 1.5098225903163627,
      part_slots_available: 48,
      max_instance_slots: 102
    },
    {
      parts_due_today: 0,
      max_quantity: 100,
      apple: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instances_due_today: 0,
      max_mango_quantity: 100,
      date: [2018, 7, 11],
      mango: {
        instances_due_today: 0,
        part_slots_available: 48,
        parts_due_today: 0,
        instance_slots_available: 102
      },
      instance_slots_available: 102,
      max_apple_quantity: 100,
      days: 30,
      multiplier: 1.5,
      part_slots_available: 48,
      max_instance_slots: 102
    }
  ]
};
</script>